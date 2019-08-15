from event import *
from itertools import chain
from operator import itemgetter
from collections.abc import Iterable


class Course:
    def __init__(self, code, name, weight=1):
        # A Course is defined by its code and its name
        self.code = code
        self.name = name
        self.weight = weight

        # A course can be composed of 5 different events: CM, TP, Exam, Oral and Other
        # Each event is classed by week
        CM = [[] for i in range(53)]  # EventCM
        TP = [[] for i in range(53)]  # EventTP
        E = [[] for i in range(53)]  # EventEXAM
        O = [[] for i in range(53)]  # EventORAL
        Other = [[] for i in range(53)]  # EventOTHER
        self.events = {EventCM:CM, EventTP:TP, EventEXAM:E, EventORAL:O, EventOTHER:Other}

    def __getitem__(self, item):
        return self.events[item]
    
    
    def __setitem__(self, name, value):
        self.events[name] = value
    

    def __eq__(self, other):
        if isinstance(other, Course):
            return self.code == other.code
        else:
            raise TypeError

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.code + ": " + self.name

    def getEvents(self, weeks=None):
        if weeks is None:
            return self.events.values()
        elif isinstance(weeks, slice) or isinstance(weeks, int) :
            return (events[weeks] for events in self.events.values())
        else:
            itg = itemgetter(*list(weeks))
            return (itg(events) for events in self.events.values())

    def getWeek(self, week):
        return tuple(self.getEvents(week))

    def join(self):
        for eventType, course in self.events.items():
            for week in range(len(course)):
                course[week].sort(key=lambda e: e.getId())
                n_events = len(course[week])
                if n_events == 0:
                    pass
                else:
                    c = [course[week][0]] # the new list of courses (joined when possible)
                    for i in range(1, n_events):
                        if c[-1].getId() == course[week][i].getId(): # If we can join [i-1] & [i]
                            id = c[-1].id[c[-1].id.index(':')+1:]
                            c[-1] = eventType(c[-1].begin, 2*c[-1].duration, self.code, self.name, c[-1].description, c[-1].location, id)
                        else:
                            c.append(course[week][i])
                    self[eventType][week] = c

    def getSummary(self, weeks=None, view=None):
        w = chain(*self.getView(weeks, view))
        if isinstance(weeks, int):
            return set(map(lambda x: x.getId(), w))
        else:
            e = chain(*w)  # [CM1, CM2,... , TP1, ...]
            return set(map(lambda x: x.getId(), e))

    def getView(self, weeks=None, ids=None):
        w = self.getEvents(weeks)
        if ids is None:
            return self.getEvents(weeks)
        else:
            ids = set(ids)
            return (list(filter(lambda e: e.getId() in ids, weekEvents)) for weekEvents in w)

    def mergeEvents(self, eventTypes, week):
        if not isinstance(eventTypes, Iterable):
            eventTypes = {eventTypes}
        view = set()
        for eventType in eventTypes: # What we merge
            to_merge = sorted(self[eventType][week], key=lambda e:e.begin)
            if len(to_merge) == 0:
                pass
            else:
                ev = [to_merge[0]]
                for e in to_merge[1:]:
                    if intersect(ev[-1], e):
                        pass
                    else:
                        ev.append(e)
                view.update(e.getId() for e in ev)
        for eventType in set(self.events.keys()) - set(eventTypes): # What we don't merge
            view.update(e.getId() for e in self[eventType][week])
        return view # A set to pass to getView function


    def addEvent(self, event):
        """
        Add an event to this course
        The event is added in the corresponding week
        If the event is already there, it is not added
        """
        week = event.getweek()
        eventType = type(event)

        if event not in self[eventType][week]:
            self[eventType][week].append(event)
            return True
        else:
            return False

    def removeEvent(self, event):
        """
        Removes an event from this course
        """
        week = event.getweek()
        eventType = type(event)

        if event not in self[eventType][week]:
            self[eventType][week].remove(event)
            return True
        else:
            return False
       

    def getEventsJSON(self):
        """
        Returns the list of events for this course, in "JSON format"
        """
        events = list()
        for course in self.events.values():
            for week in course:
                for event in week:
                    temp = {'start': str(event.begin), 'end': str(event.end), 'title': event.name, 'editable': False,
                            'description': event.name + '\n' + event.location + ' - ' + str(event.duration) + '\n' + str(
                                event.description)}
                    events.append(temp)
        return events
