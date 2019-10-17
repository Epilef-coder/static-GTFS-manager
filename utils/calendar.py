from utils.tables import readTableDB


def CombineServiceIDFromCalenderFiles():
    calendarDF = readTableDB('calendar')
    collectorSet = set()
    if len(calendarDF):
        collectorSet.update( calendarDF['service_id'].tolist() )
        # service_id_list = calendarDF['service_id'].tolist()

    calendarDatesDF = readTableDB('calendar_dates')
    if len(calendarDatesDF):
        collectorSet.update( calendarDatesDF['service_id'].tolist() )

    return list(collectorSet)