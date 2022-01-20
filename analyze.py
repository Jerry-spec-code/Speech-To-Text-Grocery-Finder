def analyze(text, trigger):
    index = text.find(trigger)
    return text[:index - 1]
