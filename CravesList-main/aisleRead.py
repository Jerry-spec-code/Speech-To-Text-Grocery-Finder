import pandas as pd

section = pd.read_csv('AisleData.csv')


def find(ingredient):
    for index in section.index:
        if ingredient == (section['Ingredients'][index]):
            if (section['Stock'][index]) == 1:
                return section['Location'][index]
            else:
                return "Not in stock"
    return "Not in stock"
