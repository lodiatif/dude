class ConstraintFailure(Exception):
    def __init__(self, message, causing_object=None):
        self.causing_object = causing_object
        super(ConstraintFailure, self).__init__(message)
