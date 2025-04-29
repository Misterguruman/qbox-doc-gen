import re
import os
import glob
from textwrap import dedent

SUCCESS = '\u2705'  # Check mark
FAILURE = '\u274C'  # Cross mark
GLOB_CHARS = {'*', '?', '[', ']'}


def _is_glob(path: str) -> bool:
    """True if the manifest path contains any glob metacharacter."""
    return any(c in path for c in GLOB_CHARS)

class Manifest:
    def __init__(self, manifest_path):
        self.manifest_path = os.path.join(manifest_path, 'fxmanifest.lua')
        self.manifest_content = self._read_manifest()
        self.resource_path = manifest_path
        self.resource = self.resource_path.split('\\')[-1]
        self.description = self._get_description()
        self.shared_scripts = self._get_shared_scripts()
        self.client_scripts = self._get_client_scripts()
        self.server_scripts = self._get_server_scripts()
        self.locales = self._get_locales()
        if self.locales:
            self.english_locale = True if 'en' in self.locales or 'en-us' in self.locales else False
        else:
            self.english_locale = False
        
        if self.english_locale and self.locales:
            if 'en' in self.locales:
                if os.path.exists(os.path.join(self.resource_path, 'locales', 'en.json')):
                    self.english_locale_path = os.path.join(self.resource_path, 'locales', 'en.json')
            elif 'en-us' in self.locales:
                if os.path.exists(os.path.join(self.resource_path, 'locales', 'en-us.json')):
                    self.english_locale_path = os.path.join(self.resource_path, 'locales', 'en-us.json')
            else:
                self.english_locale_path = None

        self._filter_imports()
        self.shared_scripts = self._expand(self.shared_scripts)
        self.client_scripts = self._expand(self.client_scripts)
        self.server_scripts = self._expand(self.server_scripts)

    def __repr__(self):
        return dedent(f"""\
            Manifest(
                resource={self.resource},
                path={self.resource_path},
                description={self.description}, 
                shared_scripts={self.shared_scripts}, 
                client_scripts={self.client_scripts}, 
                server_scripts={self.server_scripts},
                locales={self.locales},
                {SUCCESS if self.english_locale else FAILURE} english locale detected,

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

    def _get_locales(self) -> list[str]:
        if os.path.exists(os.path.join(self.resource_path, 'locales')):
            locales = os.listdir(os.path.join(self.resource_path, 'locales'))
            return [locale.split('.')[0] for locale in locales]

    def _expand(self, manifest_paths: list[str]) -> list[str]:
        """
        Expand globs relative to *self.resource_path*, return unique forward-slash
        paths in manifest order.
        """
        root_escaped = glob.escape(self.resource_path)       # ← NEW
        seen, resolved = set(), []

        for entry in manifest_paths:
            if not _is_glob(entry):
                if entry not in seen:
                    resolved.append(entry); seen.add(entry)
                continue

            # build an OS-native pattern, but the *root* part is now escaped
            pattern = os.path.join(root_escaped, *entry.split('/'))

            # recursive=True lets ** work
            for hit in sorted(glob.glob(pattern, recursive=True)):
                rel = os.path.relpath(hit, self.resource_path).replace(os.sep, '/')
                if rel not in seen:
                    resolved.append(rel); seen.add(rel)

        return resolved

