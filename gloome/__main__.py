import traceback

from gloome.config import Config


def main():
    conf = Config()
    try:
        conf.check_and_set_input_and_output_variables()
        conf.execute_calculation()
    except SystemExit:
        raise
    except BaseException as exception:
        # Anything not caught by Config.execute_action still has to leave a result.json for the web app.
        if conf.JOB_LOGGER is not None:
            conf.JOB_LOGGER.info(f'Unexpected failure -> {traceback.format_exc()}')
        conf.CALCULATED_ARGS.err_list.append(('Unexpected error', conf.describe_exception(exception)))
        conf.write_error_result()
        raise


if __name__ == '__main__':
    main()
