import os
import pandas as pd

def clearTerminal():
    os.system('cls' if os.name=='nt' else 'clear')

def certChoice() -> bool:
    certChoiceValid = False
    while not certChoiceValid:
        certChoice = input("Use custom cert? (y/n): ")
        if certChoice == 'y':
            customCert = True
            certChoiceValid = True
        elif certChoice == 'n':
            customCert = False
            certChoiceValid = True
        else:
            certChoiceValid = False
    return customCert

def saveDfToCsv(df:pd.DataFrame, fname:str):
    if fname[-4:] != '.csv':
        fname = fname + '.csv'
    df.to_csv(fname)
    return fname