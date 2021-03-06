import torch
import pandas
from transform import DataLabelCompose, ToTensor, AdditiveUniform,\
        AdditiveUniformTriary, Compose, ToType
from data_util.metagx_util import load_metagx_dataset
from data_util import util, metagx_util


class GeneDataset(torch.utils.data.Dataset):
    def __init__(self, features, labels, transform=None, binary=0):
        self.features = features
        self.labels = labels
        assert len(features) == len(labels)
        self.transform = transform
        self.binary = binary

    def __getitem__(self, idx):
        return self.transform(data=self.features.iloc[idx],
            target=self.labels.iloc[idx])

    def __len__(self):
        return len(self.features)


def get_merged_common_dataset(opt, skip_study=None, dataset_dict_cache=[], data_cache=[]):
    cancer_data_dir = opt.curated_breast_data_dir
    if dataset_dict_cache:
        dataset_dict = dataset_dict_cache[0]
    else:
        dataset_dict = util.load_curated(cancer_data_dir)
        dataset_dict_cache.append(dataset_dict)
    mergedCurated = dataset_dict['merged'].copy()

    if data_cache:
        data = data_cache[0]
    else:
        data = metagx_util.load_metagx_dataset(opt.metagx_data_dir, min_genes=opt.min_genes)
        data_cache.append(data)
    merged = data['merged'].copy()
    genes_list = data['genes_features'].copy()

    metagx_pos_outcome = merged[merged.posOutcome.isin([-1, 1])]
    print('num pos outcome studies {0}'.format(len(metagx_pos_outcome.study.unique())))
    if skip_study is not None:
        study_to_skip = metagx_pos_outcome.study.unique()[skip_study]
    else:
        study_to_skip = None

    merged_common = util.merge_metagx_curated(merged, mergedCurated)

    merged_treatments = list(metagx_util.treatment_columns_metagx) + util.treatment_columns_bmc
    merged_treatments = [x for x in merged_treatments if x in merged_common]
    merged_treatments = list(set(merged_treatments))
    # add continious covariates to genes
    cont_columns = [x for x in merged_treatments if len(merged_common[x].unique()) > 20]
    merged_treatments = [x for x in merged_treatments if x not in cont_columns]
    common_genes_list = [x for x in genes_list if x in merged_common]
    if opt.use_covars:
        non_genes = cont_columns + merged_treatments + ['posOutcome']
    else:
        non_genes = []
    if study_to_skip is None:
        train_data, train_labels, val_data, val_labels = util.random_split(merged_common,
                                                              common_genes_list + non_genes,
                                                              ['study', 'posOutcome'],
                                                              balance_validation=False,
                                                              balance_by_study=False,
                                                              ratio=opt.test_ratio,
                                                              to_numpy=False)
    else:
        train_data, train_labels, val_data, val_labels = next(util.split_by_study(merged_common,
                                                              common_genes_list + non_genes,
                                                              ['study', 'posOutcome'],
                                                              study=study_to_skip,
                                                              to_numpy=False))
        # it's ok to use gene expression in unsupervised model
        copy = val_data.copy()
        copy.loc[:, non_genes] = 0
        val_copy = val_labels.copy()
        val_copy.loc[:, 'posOutcome'] = 0
        train_data = pandas.concat([train_data, copy], ignore_index=True)
        train_labels = pandas.concat([train_labels, val_copy], ignore_index=True)
        print('validation study {0}'.format(study_to_skip))
        print(val_data.shape)

    train_data.fillna(0, inplace=True)
    val_data.fillna(0, inplace=True)
    to_tensor = ToTensor()
    to_float = ToType('float')
    add_age = AdditiveUniform(-0.5, 0.5, 'age')
    add_tumor_size = AdditiveUniform(-0.5, 0.5, 'tumor_size')
    add_posOutcome = AdditiveUniformTriary(0.0, 0.05, 'posOutcome')
    add_treat = Compose([AdditiveUniformTriary(0.0, 0.05, x) for x in merged_treatments])
    lst = []
    if 'posOutcome' in train_data.columns:
        lst = [add_age, add_tumor_size, add_posOutcome, add_treat]
    compose = Compose(lst + [to_tensor, to_float])
    compose_label = Compose([add_posOutcome, to_tensor, to_float])
    num_binary = len(merged_treatments + ['posOutcome'])
    num_binary = 0
    transform = DataLabelCompose(compose, compose_label)

    train_set = GeneDataset(train_data, train_labels, transform, binary=num_binary)
    test_set = GeneDataset(val_data, val_labels, transform, binary=num_binary)
    return train_set, test_set


def get_metagx_dataset(ratio=0.1):
    data = load_metagx_dataset('/home/noskill/projects/cancer/data/metaGxBreast/', min_genes=5000)
    merged = data['merged']
    genes_list = data['genes_features']

    train_data, train_labels, val_data, val_labels = util.random_split(merged,
                                                              genes_list,
                                                              ['study'],
                                                              balance_validation=False,
                                                              balance_by_study=False,
                                                              ratio=ratio)
    to_tensor = ToTensor()
    transform = DataLabelCompose(to_tensor, to_tensor)

    # assert val_labels.mean() == 0.5
    train_set = GeneDataset(train_data, train_labels, transform)
    test_set = GeneDataset(val_data, val_labels, transform)
    return train_set, test_set


