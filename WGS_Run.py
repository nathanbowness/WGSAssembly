from WGSAssembly import Assemble

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", action="store_true",
                        help="Don't ask to update redmine api key")

    args = parser.parse_args()
    assembly = Assemble(args.force)

    # try to run the assembler, if an error occurs print it
    try:
        assembly.timed_retrieve()
    except Exception as e:
        import traceback
        assembly.timelog.time_print("[Error] Dumping...\n%s" % traceback.format_exc())
        raise
