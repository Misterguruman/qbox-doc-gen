import re
import os
from textwrap import dedent

SUCCESS = '\u2705'  # Check mark
FAILURE = '\u274C'  # Cross mark

class Manifest:
    def __init__(self, manifest_path):
        self.manifest_path = os.path.join(manifest_path, 'fxmanifest.lua')
        self.manifest_content = self._read_manifest()
        self.resource_path = os.path.dirname(manifest_path)
        self.resource = self.resource_path.split('\\')[-1]
        self.description = self._get_description()
        self.shared_scripts = self._get_shared_scripts()
        self.client_scripts = self._get_client_scripts()
        self.server_scripts = self._get_server_scripts()
        self._filter_imports()

    def __repr__(self):
        return dedent(f"""\
            Manifest(
                resource={self.resource},
                path={self.resource_path},
                description={self.description}, 
                shared_scripts={self.shared_scripts}, 
                client_scripts={self.client_scripts}, 
                server_scripts={self.server_scripts},

                imports:
                {SUCCESS if self.uses_ox_lib else FAILURE} ox_lib,
                {SUCCESS if self.uses_oxmysql else FAILURE} oxmysql,
                {SUCCESS if self.uses_qbx_lib else FAILURE} qbx_lib,
                {SUCCESS if self.uses_qbx_playerdata else FAILURE} qbx_playerdata,
            )"""
        )

    def _read_manifest(self):
        try:
            with open(self.manifest_path, 'r') as file:
                return file.read()
        except OSError as e:
            raise Exception(f"Error reading manifest file: {e}")

    def _get_description(self) -> str:
        description_match = re.search(r"^description\s*['|\"](.*)['|\"]\s*$", self.manifest_content, re.MULTILINE)
        if description_match:
            return description_match.group(1)
        else:
            return "No description found"
        
    def _get_shared_scripts(self) -> list[str]:
        shared_script_match = re.search(r"^shared_script\s*['|\"](.*)['|\"]\s*$", self.manifest_content, re.MULTILINE)
        if shared_script_match:
            return [shared_script_match.group(1)]

        else:
            shared_scripts_match = re.search(r"^shared_scripts\s*\{([^}]*)\}", self.manifest_content, re.MULTILINE | re.DOTALL)
            if shared_scripts_match:
                return re.findall(r'[\"\']([^\"\']+)[\"\']', shared_scripts_match.groups()[0], re.MULTILINE | re.DOTALL)
            else: 
                return []
            
    def _get_client_scripts(self) -> list[str]:
        client_script_match = re.search(r"^client_script\s*['|\"](.*)['|\"]\s*$", self.manifest_content, re.MULTILINE)
        if client_script_match:
            return [client_script_match.group(1)]
        else:
            client_scripts_match = re.search(r"^client_scripts\s*\{([^}]*)\}", self.manifest_content, re.MULTILINE | re.DOTALL)
            if client_scripts_match:
                return re.findall(r'[\"\']([^\"\']+)[\"\']', client_scripts_match.groups()[0], re.MULTILINE | re.DOTALL)
            
            else: 
                return []
            
    def _get_server_scripts(self) -> list[str]:
        server_script_match = re.search(r"^server_script\s*['|\"](.*)['|\"]\s*$", self.manifest_content, re.MULTILINE)
        if server_script_match:
            return [server_script_match.group(1)]
        else:
            server_scripts_match = re.search(r"^server_scripts\s*\{([^}]*)\}", self.manifest_content, re.MULTILINE | re.DOTALL)
            if server_scripts_match:
                return re.findall(r'[\"\']([^\"\']+)[\"\']', server_scripts_match.groups()[0], re.MULTILINE | re.DOTALL)
            else: 
                return []
            
    def _filter_imports(self):
        if '@ox_lib/init.lua' in self.shared_scripts:
            self.shared_scripts.remove('@ox_lib/init.lua')
            self.uses_ox_lib = True
        else:
            self.uses_ox_lib = False

        if '@qbx_core/modules/lib.lua' in self.shared_scripts:
            self.shared_scripts.remove('@qbx_core/modules/lib.lua')
            self.uses_qbx_lib = True
        else:
            self.uses_qbx_lib = False

        if '@oxmysql/lib/MySQL.lua' in self.server_scripts:
            self.server_scripts.remove('@oxmysql/lib/MySQL.lua')
            self.uses_oxmysql = True
        else:
            self.uses_oxmysql = False

        if '@qbx_core/modules/playerdata.lua' in self.client_scripts:
            self.client_scripts.remove('@qbx_core/modules/playerdata.lua')
            self.uses_qbx_playerdata = True
        else:
            self.uses_qbx_playerdata = False

        shared_imports = [x for x in self.shared_scripts if x.startswith('@')]
        for import_ in shared_imports:
            self.shared_scripts.remove(import_)

        client_imports = [x for x in self.client_scripts if x.startswith('@')]
        for import_ in client_imports:
            self.client_scripts.remove(import_)

        server_imports = [x for x in self.server_scripts if x.startswith('@')]
        for import_ in server_imports:
            self.server_scripts.remove(import_)

        self.uncommon_imports = list(set(shared_imports + client_imports + server_imports))