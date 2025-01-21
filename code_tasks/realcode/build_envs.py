from realcode_eval.prepare_data.run import build_envs

if __name__ == '__main__':
    dataset_dir = 'data/realcode_v3'
    build_envs(dataset_dir, n_jobs=8)
    print('Done')
