from sklearn.metrics import recall_score, precision_score, f1_score, confusion_matrix
from sklearn.metrics import roc_curve, auc


def compute_metrics(result, y_true, y_pred):
    result['recall'].append(recall_score(y_true, y_pred))
    result['precision'].append( precision_score(y_true, y_pred))
    result['f1'].append(f1_score(y_true, y_pred))
    result['confusion'].append(confusion_matrix(y_true, y_pred, labels=[0,1]))
    confusion = result['confusion'][-1]
    accuracy = (confusion[0][0] + confusion[1][1]) / (sum(confusion[0]) + sum(confusion[1]))
    result['accuracy'].append(accuracy)


def compute_auc(result, y_true, y_pred):
    fpr, tpr, thresholds = roc_curve(y_true, y_pred)
    result['auc'].append(auc(fpr, tpr))
