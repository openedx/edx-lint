"""The edx_lint write command."""

from edx_lint.write import write_file

def write_main(argv):
    """
    write FILENAME
        Write a local copy of FILENAME using FILENAME_tweaks for local tweaks.
    """
    if len(argv) != 1:
        print("Please provide the name of a file to write.")
        return 1

    filename = argv[0]
    ret = write_file(filename, output_fn=print)
    return ret
