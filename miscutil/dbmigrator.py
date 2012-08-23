# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Database migration command-line tool

python dbmigrator.py --create-migration=~/src/openaire/openaire/migrations/
python dbmigrator.py --migration-history
python dbmigrator.py --migrate-show
python dbmigrator.py --migrate

Recommendations for writing migrations:

 * Once a migration have been committed to master, not fiddling is allowed 
   afterwards. If you want to correct a mistake, make a new migration instead. 
 * All migrations must depend on a previous migration (except for your first 
   migration.
 * The first migration should be empty and named 'xxxxxx_baseline.py'
 * For every software release, make a 'xxxxxx_baseline_xyz.py' that 
   depends on all migrations between the previous baseline and the new, so future 
   migration can depend on this baseline.
"""

from optparse import OptionParser, Option, IndentedHelpFormatter, OptionGroup
import os
import random
import string
import sys

from invenio.textutils import wrap_text_in_a_box, wait_for_user

MIGRATION_TEMPLATE = """# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.dbmigrator_utils import DbMigration, run_sql_ignore, run_tabcreate
from invenio.dbquery import run_sql

class Migration( DbMigration ):
    \"\"\" Short description of migration \"\"\"
    
    module = ''
    \"\"\" Module name (leave empty if Invenio) \"\"\"
    
    depends_on = ['baseline']
    \"\"\" Every migration must depend on at least one previous migration \"\"\"
    
    def forward(self):
        \"\"\" Put your run_sql queries here \"\"\"
        pass
"""


def migration_id():
    """ Generate a new migration id. """
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))


def cli_cmd_migrate():
    """ Command for running applying migrations """
    try:
        from invenio.dbmigrator_utils import InvenioMigrator
                
        migrator = InvenioMigrator()
        migrations = migrator.get_migrations()
        
        if not migrations:
            print ">>> All migrations have been applied."
            sys.exit(0)
        
        print ">>> Following migrations will be applied:"
        
        for m in migrations:
            print ">>> * %s%s" % (m.id, m.get_doc())
        
        wait_for_user(wrap_text_in_a_box("""WARNING: You are going to migrate your database!"""))
        
        for m in migrations:
            print ">>> Applying %s%s" % (m.id, m.get_doc())
            try:
                migrator.apply(m)
            except Exception, e:
                ">>> Migration of %s failed. Your database is in an inconsistent state. Please manually review the migration and resolve inconsistencies." % m.id
                print e.message
                sys.exit(1)
        
        print ">>> Migration completed successfully."
    except Exception, e:
        print e.message
        sys.exit(1)


def cli_cmd_migrate_show():
    """ Command for showing migrations ready to be applied """
    try:
        from invenio.dbmigrator_utils import InvenioMigrator
                
        migrator = InvenioMigrator()
        migrations = migrator.get_migrations()
        
        if not migrations:
            print ">>> All migrations have been applied."
            sys.exit(0)
        
        print ">>> Following migrations are ready to be applied:"
        
        for m in migrations:
            print ">>> * %s%s" % (m.id, m.get_doc())
    except Exception, e:
        print e.message
        sys.exit(1)


def cli_cmd_migration_history():
    """ Command for showing all migrations already applied. """
    try:
        from invenio.dbmigrator_utils import InvenioMigrator
                
        migrator = InvenioMigrator()
        migrations = migrator.get_history()
        
        if not migrations:
            print ">>> No migrations have been applied."
            sys.exit(0)
        
        print ">>> Following migrations have been applied:"
        
        for m_id, applied in migrations:
            print ">>> * %s (%s)" % (m_id, applied)
    except Exception, e:
        print e.message
        sys.exit(1)


def cli_cmd_create_migration(path):
    """
    Create a new migration with a unique id (for developers).
    """
    try:
        path = os.path.expandvars(os.path.expanduser(path))
        
        if not os.path.exists(path):
            raise Exception("Path does not exists: %s" % path)
        if not os.path.isdir(path):
            raise Exception("Path is not a directory: %s" % path)
        
        i = 0
        while True:
            migration_file = os.path.join(path, "%s_migration.py" % migration_id())
            if not os.path.exists( migration_file ):
                break
            elif i > 100:
                raise Exception("Could not generate unique migration id.")
            i += 1
        
        # `Write migration template
        f = open(migration_file,'w')
        f.write(MIGRATION_TEMPLATE)
        f.close()
        
        print ">>> Created new migration %s" % migration_file
    except Exception, e:
        print e.message
        sys.exit(1)


#
# Below has more or less copy/pasted from inveniocfg.
#


def prepare_option_parser():
    """Parse the command line options."""
    class InvenioOption(Option):
        """
        Option class that implements the action 'store_append_const' which will
        
        1) append <const> to list in options.<dest>
        2) take a value and store in options.<const>
        
        Useful for e.g. appending a const to an actions list, while also taking an option
        value and storing it.
        
        This ensures that we can run actions in the order they are given on the command-line.
        """
        ACTIONS = Option.ACTIONS + ("store_append_const",)
        STORE_ACTIONS = Option.STORE_ACTIONS + ("store_append_const",)
        TYPED_ACTIONS = Option.TYPED_ACTIONS + ("store_append_const",)
        ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("store_append_const",)
        CONST_ACTIONS = Option.CONST_ACTIONS + ("store_append_const",)
        
        def take_action(self, action, dest, opt, value, values, parser):
            if action == "store_append_const":
                # Combination of 'store' and 'append_const' actions
                values.ensure_value(dest, []).append(self.const)
                value_dest = self.const.replace('-', '_')
                setattr(values, value_dest, value)
            else:
                Option.take_action(self, action, dest, opt, value, values, parser)
        
    parser = OptionParser( option_class=InvenioOption, description="Invenio database migration CLI tool", formatter=IndentedHelpFormatter(max_help_position=31) )
    
    migrate_options = OptionGroup(parser, "Options to migrate your installation")
    migrate_options.add_option( "", "--migrate", dest='actions', const='migrate', action="append_const", help="apply migrations" )
    migrate_options.add_option( "", "--migrate-show", dest='actions', const='migrate-show', action="append_const", help="show migrations to be applied" )
    migrate_options.add_option( "", "--migration-history", dest='actions', const='migration-history', action="append_const", help="show all migrations already applied" )
    migrate_options.add_option( "", "--create-migration", dest='actions', metavar='DIR', const='create-migration', action="store_append_const", help="create a new migration (for developers)" )
    parser.add_option_group( migrate_options )
    
    parser.add_option('--yes-i-know', action='store_true', dest='yes-i-know', help='use with care!')
    
    return parser


def main(*cmd_args):
    """Main entry point."""
    # Allow easier testing
    if not cmd_args:
        cmd_args = sys.argv[1:]
    
    # Parse arguments
    parser = prepare_option_parser()
    (options, args) = parser.parse_args( list(cmd_args) )
    
    actions = getattr(options, 'actions', None)
    
    if not actions:
        print """ERROR: Please specify a command.  Please see '--help'."""
        sys.exit(1)
    
    for action in actions:
        if action == 'migrate':
            cli_cmd_migrate()
        elif action == 'migrate-show':
            cli_cmd_migrate_show()
        elif action == 'migration-history':
            cli_cmd_migration_history()
        elif action == 'create-migration':
            cli_cmd_create_migration(getattr(options, 'create_migration', None))

if __name__ == '__main__':
    main()
