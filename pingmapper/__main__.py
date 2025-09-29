
import os, sys

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

# Default function to run
if len(sys.argv) == 1:
    to_do = 'gui'
else:
    to_do = sys.argv[1]

# May need to load conda config, check later

def main(process):

    from pingmapper.version import __version__
    print("\n\nPINGMapper v{}".format(__version__))
    
    # Process single sonar log
    if process == 'gui':
        print('\n\nLaunching gui for processing single sonar log...\n\n')
        # from pingmapper.gui_main import gui
        # gui()
        from pingmapper.gui_main import gui
        gui(batch=False)


    # Batch process sonar logs
    elif process == 'gui_batch':
        print('\n\nLaunching gui for batch processing sonar logs...\n\n')
        from pingmapper.gui_main import gui
        gui(batch=True)

    # Do test on small dataset
    elif process == 'test':
        print('\n\nTesting PINGMapper on small dataset...\n\n')
        from pingmapper.test_PINGMapper import test
        test(1)

    # Do test on large dataset
    elif process == 'test_large':
        print('\n\nTesting PINGMapper on large dataset...\n\n')
        from pingmapper.test_PINGMapper import test
        test(2)

if __name__ == "__main__":
    main(to_do)