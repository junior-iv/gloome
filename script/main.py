# progress_bar = {'value': 0}
# while progress_bar.get('value', 0) < 100:
#     progress_bar.update({'value': progress_bar.get('value', 0) + 20})
#     print(progress_bar.get('value', 0))
# import os
# os.path.join(os.getcwd(), "gloome")

from .config import Config

if __name__ == '__main__':
    config = Config()
    config.check_and_set_input_and_output_variables()
    # print(vars(config))
    # import inspect
    #
    # print(vars(config))
    # parser = argparse.ArgumentParser()
    # parser.add_argument('path',
    #                     help='A path to a folder in which the sweeps analysis will be written.',
    #                     type=lambda path: path if path.exists(path) else parser.error(f'{path} does not exist!'))
    # parser.add_argument('jobID', type=str,
    #                     help='The size of a window to which a score will be computed')
    #
    # args = parser.parse_args()
    #
    # results_dir = path.join('/bioseq/data/results/effectidor', args.jobID)
    # endFile = path.join(results_dir, 'out_learning', 'concensus_predictions_with_annotation.csv')
    # if path.exists(endFile):
    #     status = 'PASS'
    # else:
    #     status = 'FAIL'
    #
    # results_url = f'http://effectidor.tau.ac.il/results/{args.jobID}/output.html'
    # date = datetime.datetime.today().strftime('%d%m%Y')
    # with open(os.path.join(args.path, f'effectidor_{date}.txt'), "w") as f:
    #     f.write(f'{status},{results_url}')
    # f.close()
