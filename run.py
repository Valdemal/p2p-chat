import sys
import importlib.util
import subprocess

reqModules = ['socket', 'threading', 'curses', 'npyscreen', 'time', 'datetime', 'io', 'os', 'pyperclip'] # Array with required modules
missingModules = [] # Array to fill with missing modules
missing = 0 # Missing module counter | Will be replaced by len(missingModules)

if sys.version_info < (3, 3): # Check the python version
    print("Python version 3.3 is required to run p2p-chat. Your version is {0}.".format(sys.version))
    exit(1)
else:
    for module in reqModules: # Go through each module and check if its installed
        if not module in sys.modules and importlib.util.find_spec(module) == None:
            missing += 1
            missingModules.append(module)
            print("Required module not found: {0}".format(module))
        else:
            print("{0} is installed".format(module))

    if missing > 0: # If there are any missing modules, try and install them | Installation requires pip
        print("At least one required module is missing. Exiting...")
        if "pip" in sys.modules or importlib.util.find_spec("pip") is not None:
            answ = input("Should we try and install missing modules with pip? [y/n] >> ")
            if answ == "y" or answ == "Y":
                for module in missingModules:
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                    except Exception:
                        pass
                    if not module in sys.modules and importlib.util.find_spec(module) == None:
                        print("Failed to install {0}.".format(module))
                    else:
                        print("Installed {0}.".format(module))
                        missing -= 1
                        missingModules.remove(module)
                if missingModules == 0:
                    print("All modules have been installed.")
                else:
                    print("At least one installation failed. Please try to install these modules manually:")
                    for module in missingModules:
                        print(module)
                    exit(1)
            else:
                print("Please try to install these modules manually:")
                for module in missingModules:
                    print(module)
                    exit(1)     
        else:
            print("Please try to install these modules manually:")
            for module in missingModules:
                print(module)
                exit(1)
    

import chat # Import the Chat App
chatApp = chat.ChatApp().run() # Run the Chat App



