import pandas as pd
import requests
import shutil
import os
import  numpy as np
def read_document(document_URL, id):
    shutil.rmtree("./cache",ignore_errors=True)
    r = requests.get(document_URL)
    open(f'file{id}.csv', 'wb').write(r.content)
    X_test = pd.read_csv(f'file{id}.csv',sep='\t')
    os.remove(f'file{id}.csv')
    return X_test
def get_predict(model, X_test, mode,id):
    predict = model.predict(X_test)
    if mode == 'csv':
       np.savetxt(f'predict{id}.csv', predict, delimiter='\t')
       return
    else:
        return predict