from os.path import dirname
import csv
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.auth.models import User
from OpenTreeMap.treemap.models import Species, Tree, Neighborhood, ZipCode, TreeFlags, Choices, ImportEvent

class Command(BaseCommand):
    args = '<input_file_name, data_owner_id, base_srid>'
    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose debug text'),
    )

    def get_dbf_rows(self, in_file):
        reader = dbf.Dbf(in_file)
        print 'Opening input file: %s ' % in_file

        self.headers = reader.fieldNames
        self.err_writer.writerow(self.headers)
        
        print 'Converting input file to dictionary'
        rows = []
        for dbf_row in reader:
            d = {}
            for name in self.headers:
                d[name] = dbf_row[name]
            rows.append(d)
        return rows
    
    def get_csv_rows(self, in_file):
        reader = csv.DictReader(open(in_file, 'r' ), restval=123)
        print 'Opening input file: %s ' % in_file

        rows = list(reader)
                
        self.headers = reader.fieldnames
        self.err_writer.writerow(self.headers)        
                
        return rows
    
    def handle(self, *args, **options):
        try:    
            self.file_name = args[0]
            in_file =  self.file_name
            err_file =  self.file_name + ".err"
            self.verbose = options.get('verbose')
            self.user_id = args[1]
            if len(args) > 2:
                self.base_srid = int(args[2])
                self.tf = CoordTransform(SpatialReference(self.base_srid), SpatialReference(4326))
                print "Using transformaton object: %s" % self.tf
            else:
                self.base_srid = 4326
        except:
            print "Arguments:  Input_File_Name.[dbf|csv], Data_Owner_User_Id, (Base_SRID optional)"
            print "Options:    --verbose"
            return
        
        self.err_writer = csv.writer(open(err_file, 'wb'))
        
        if self.file_name.endswith('.csv'):
            rows = self.get_csv_rows(in_file)
        if self.file_name.endswith('.dbf'):
            rows = self.get_dbf_rows(in_file)

        self.data_owner = User.objects.get(pk=self.user_id)
        self.updater = User.objects.get(pk=1)
        
        self.import_event = ImportEvent(file_name=self.file_name)
        self.import_event.save()
        
        print 'Importing %d records' % len(rows)
        for i, row in enumerate(rows):
            self.handle_row(row)
            
            j = i + 1
            if j % 50 == 0:
               print 'Loaded %d...' % j
            self.log_verbose("item %d" % i)
        
        print "Finished data load. "

        print "Calculating new species tree counts... "
        for s in Species.objects.all():
            s.save()
        print "Done."
    
    def log_verbose(self, msg):
        if self.verbose: print msg
    
    def log_error(self, msg, row):
        print "ERROR: %s" % msg
        columns = [row[s] for s in self.headers]
        self.err_writer.writerow(columns)
    
    def check_coords(self, row):
        try:
            x = float(row.get('POINT_X', 0))
            y = float(row.get('POINT_Y', 0))
        except:
            self.log_error("  Invalid coords, might not be numbers", row)
            return (False, 0, 0)

        ok = x and y
        if not ok:
            self.log_error("  coords ok", row)
        self.log_verbose("  Passed coordinate check")
        return (ok, x, y)

    def check_species(self, row):
        # locate the species and instanciate the tree instance
        if not row.get('SCIENTIFIC') and not row.get('GENUS'):            
            self.log_verbose("  No species information")
            return (True, None)

        if row.get('SCIENTIFIC'):
            name = str(row['SCIENTIFIC']).strip()
            species = Species.objects.filter(scientific_name__iexact=name)
            self.log_verbose("  Looking for species: %s" % name)
        else:
            genus = str(row['GENUS']).strip()
            species = ''
            cultivar = ''
            if row.get('SPECIES'):
                species = str(row['SPECIES']).strip()
            if row.get('CULTIVAR'):
                cultivar = str(row['CULTIVAR']).strip()
            species = Species.objects.filter(genus__iexact=genus).filter(species__iexact=species).filter(cultivar_name__iexact=cultivar)
            self.log_verbose("  Looking for species: %s %s %s" % (genus, species, cultivar))
        

        if species: #species match found
            self.log_verbose("  Found species %r" % species[0])
            return (True, species)
            
        #species data but no match, check it manually
        self.log_error("ERROR:  Unknown species %r" % name, row) 
        return (False, None)

    def check_proximity(self, tree, species, row):
        # check for nearby trees
        collisions = tree.validate_proximity(True, 0)
        
        # if there are no collisions, then proceed as planned
        if not collisions:
            self.log_verbose("  No collisions found")
            return (True, tree)
        self.log_verbose("  Initial proximity test count: %d" % collisions.count())
        
        # exclude collisions from the same file we're working in
        collisions = collisions.exclude(import_event=self.import_event)
        if not collisions:
            self.log_verbose("  All collisions are for from this import file")
            return (True, tree)                
        self.log_verbose("  Secondary proximity test count: %d" % collisions.count())
        
        # if we have multiple collitions, check for same species or unknown species
        # and try to associate with one of them otherwise abort
        if collisions.count() > 1:
            
            # Precedence: single same species, single unknown 
            # return false for all others and log
            if species:                
                same = collisions.filter(species=species[0])            
                if same.count() == 1 and same[0].species == species[0]:
                    self.log_verbose("  Using single nearby tree of same species")
                    return (True, same[0])
            
            unk = collisions.filter(species=None)
                
            if unk.count() == 1:
                self.log_verbose("  Using single nearby tree of unknown species")
                return (True, unk[0])
            
            self.log_error("ERROR:  Proximity test failed (near %d trees)" % collisions.count(), row)
            return (False, None)

        # one nearby match found, use it as base
        tree = collisions[0]
        self.log_verbose("  Found one tree nearby")

        # if neither have a species, then we're done and we need to use
        # the tree we collided with.
        if not tree.species and not species:
            self.log_verbose("  No species info for either record, using %d as base record" % tree.id)
            return (True, tree)

        # if only the new one has a species, update the tree we collided
        # with and then return it
        if not tree.species:
            # we need to update the collision tree with the new species
            tree.set_species(species[0].id, False) # save later
            self.log_verbose("  Species match, using update file species: %s" % species[0])
            return (True, tree)

        # if only the collision tree has a species, we're done.
        if not species or species.count() == 0:
            self.log_verbose("  No species info for import record, using %d as base record" % tree.id)
            return (True, tree)

        # in this case, both had a species. we should check to see if
        # the species are the same.
        if tree.species != species[0]:
            # now that we have a new species, we want to update the
            # collision tree's species and delete all the old status
            # information.
            self.log_verbose("  Species do not match, using update file species: %s" % species[0])
            tree.set_species(species[0].id, False)
            TreeStatus.objects.filter(tree=tree.id).delete()
        return (True, tree) 
    
    def handle_row(self, row):
        self.log_verbose(row)

        # check the physical location
        ok, x, y = self.check_coords(row)
        if not ok: return

        # check the species (if any)
        ok, species = self.check_species(row)
        if not ok: return

        # check the proximity (try to match up with existing trees)
        if (species):
            tree = Tree(species=species[0])
        else:
            tree = Tree()
        
        try:
            if (self.base_srid != 4326):
                geom = Point(x, y, srid=self.base_srid)
                geom.transform(self.tf)
                self.log_verbose(geom)
                tree.geometry = geom
            else:        
                tree.geometry = Point(x, y, srid=4326)
        except:
            self.log_error("ERROR: Geometry failed to transform", row)
            return
        
        ok, tree = self.check_proximity(tree, species, row)
        if not ok: return

        if row.get('ADDRESS') and not tree.address_street:
            tree.address_street = str(row['ADDRESS']).title()
            tree.geocoded_address = str(row['ADDRESS']).title()
        
        if not tree.geocoded_address: 
            tree.geocoded_address = ""
            
            
        # FIXME: get this from the config?
        tree.address_state = 'CA'

        tree.import_event = self.import_event
        tree.last_updated_by = self.updater
        tree.data_owner = self.data_owner
        tree.owner_additional_properties = self.file_name
        if row.get('ID'):
            tree.owner_orig_id = row['ID']
        
        if row.get('ORIGID'):
            tree.owner_additional_properties = "ORIGID=" + str(row['ORIGID'])

        if row.get('PLOTTYPE'):
            for k, v in Choices().get_field_choices('plot'):
                if v == row['PLOTTYPE']:
                    tree.plot_type = k
                    break;
        if row.get('PLOTLENGTH'): 
            tree.plot_length = row['PLOTLENGTH']

        if row.get('PLOTWIDTH'): 
            tree.plot_width = row['PLOTWIDTH']            

        # if powerline is specified, then we want to set our boolean
        # attribute; otherwise leave it alone.
        powerline = row.get('POWERLINE')
        if powerline is None or powerline.strip() == "":
            pass
        elif powerline is True or powerline.lower() == "true" or powerline.lower() == 'yes':
            tree.powerline_conflict_potential = 'Yes'
        else:
            tree.powerline_conflict_potential = 'No'

        sidewalk_damage = row.get('SIDEWALK')
        if sidewalk_damage is None or sidewalk_damage.strip() == "":
            pass
        elif sidewalk_damage is True or sidewalk_damage.lower() == "true" or sidewalk_damage.lower() == 'yes':
            tree.sidewalk_damage = 2
        else:
            tree.sidewalk_damage = 1

        if row.get('OWNER'):
            tree.tree_owner = str(row["OWNER"])

        if row.get('STEWARD'):
            tree.steward_name = str(row["STEWARD"])

        if row.get('SPONSOR'):
            tree.sponsor = str(row["SPONSOR"])

        if row.get('DATEPLANTED'):
            date = str(row['DATEPLANTED'])
            date = datetime.strptime(date, "%m/%d/%Y")
            tree.date_planted = date.strftime("%Y-%m-%d")

        if row.get('DIAMETER'):
            tree.dbh = float(row['DIAMETER'])

        if row.get('HEIGHT'):
            tree.height = float(row['HEIGHT'])

        if row.get('CANOPYHEIGHT'):
            tree.canopy_height = float(row['CANOPYHEIGHT'])

        if row.get('CONDITION'):
            for k, v in Choices().get_field_choices('condition'):
                if v == row['CONDITION']:
                    tree.condition = k
                    break;

        if row.get('CANOPYCONDITION'):
            for k, v in Choices().get_field_choices('canopy_condition'):
                if v == row['CANOPYCONDITION']:
                    tree.canopy_condition = k
                    break;


        pnt = tree.geometry

        n = Neighborhood.objects.filter(geometry__contains=pnt)
        z = ZipCode.objects.filter(geometry__contains=pnt)
        
        if n:
            tree.neighborhoods = ""
            for nhood in n:
                if nhood:
                    tree.neighborhoods = tree.neighborhoods + " " + nhood.id.__str__()
        else: 
            tree.neighborhoods = ""

        tree.quick_save()

        tree.neighborhood.clear()
        tree.zipcode = None
        if n:
            for nhood in n:
                if nhood:
                    tree.neighborhood.add(nhood)
        if z: tree.zipcode = z[0]

        if row.get('PROJECT_1'):
            for k, v in Choices().get_field_choices('local'):
                if v == row['PROJECT_1']:
                    local = TreeFlags(key=k,tree=tree,reported_by=self.updater)
                    local.save()
                    break;
        if row.get('PROJECT_2'):            
            for k, v in Choices().get_field_choices('local'):
                if v == row['PROJECT_2']:
                    local = TreeFlags(key=k,tree=tree,reported_by=self.updater)
                    local.save()
                    break;
        if row.get('PROJECT_3'):           
            for k, v in Choices().get_field_choices('local'):
                if v == row['PROJECT_3']:
                    local = TreeFlags(key=k,tree=tree,reported_by=self.updater)
                    local.save()
                    break;


        # rerun validation tests and store results
        tree.validate_all()

