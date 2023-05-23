import sys
import importlib.util
import subprocess
import os

required_modules = ['socket', 'threading', 'curses', 'npyscreen', 'time', 'datetime', 'pyperclip', 'pathlib']
missing_modules = []

required_python_version = (3, 3)

if sys.version_info < required_python_version:  # Check the python version
    print(f"Python version {required_python_version[0]}.{required_python_version[1]}"
          f" is required to run p2p-chat. Your version is {sys.version}.")
    exit(1)
else:
    # Go through each module and check if its installed
    for module in required_modules:
        if module not in sys.modules and importlib.util.find_spec(module) is None:
            missing_modules.append(module)
            print("Required module not found: {0}".format(module))
        else:
            print("{0} is installed".format(module))

    if missing_modules:  # If there are any missing modules, try and install them | Installation requires pip
        print("At least one required module is missing. Exiting...")
        if "pip" in sys.modules or importlib.util.find_spec("pip") is not None:
            answer = input("Should we try and install missing modules with pip? [y/n] >> ")
            if answer == "y" or answer == "Y":
                for module in missing_modules:
                    if module == "curses" and os.name == "nt":
                        print("Curses needs to be installed manually. See https//github.com/F1xw/p2p-chat#Requirements")
                        continue
                    try:
                        pip = subprocess.Popen([sys.executable, "-m", "pip", "install", module])
                        pip.wait()
                    except Exception:
                        pass

                    if module not in sys.modules and importlib.util.find_spec(module) is None:
                        print("Failed to install {0}.".format(module))
                    else:
                        print("Installed {0}.".format(module))
                        missing_modules.remove(module)

if missing_modules:
    print("Please try to install these modules manually:")
    for module in missing_modules:
        print("-", module)
        i = input("Press Enter to Exit >>")
        exit(1)
else:
    import chat

    chatApp = chat.ChatApp().run()  # Run the Chat App
