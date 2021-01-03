
import dataclasses as dc
import logging
import typing
from collections import namedtuple

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.INFO)

FlufParameter = namedtuple('FlufParameter',
                           ['name', 'default', 'validator', 'help'])


class FlufAPI:
    """ Placeholder for API functions """
    pass


@dc.dataclass
class FlufApp:

    parameters: typing.List[FlufParameter] \
        = dc.field(default_factory=list)

    datatypes: typing.Dict = dc.field(default_factory=dict)

    functions: typing.List[typing.Callable] \
        = dc.field(default_factory=list)

    config: typing.Dict = dc.field(default_factory=dict)

    api: FlufAPI = dc.field(default_factory=FlufAPI)

    def define_parameter(self, name, default, validator=str, help=""):

        self.parameters.append(
            FlufParameter(name=name, validator=validator,
                          default=default, help=help))

    def register_datatype(self, dt):
        if dt.name in self.datatypes:
            lgr.warning(f"Overriding datatype {dt.name}!")

        lgr.debug(f"register datatype {dt}")
        self.datatypes[dt.name] = dt

    def validate_config(self):
        for p in self.parameters:
            curval = self.config.get(p.name, p.default)
            curval = p.validator(curval)
            self.config[p.name] = curval

    def validate_config_custom(self, config):
        for p in self.parameters:
            curval = config.get(p.name, p.default)
            curval = p.validator(curval)
            config[p.name] = curval
        return config

    def show_parameters(self):
        for p in self.parameters:
            print(p.name, self.config[p.name])

    def get_parameter_all(self, key):
        for p in self.parameters:
            if p.name == key:
                return p, key, self.config[key]

    def get_parameter(self, key):
        param, key, value = self.get_parameter_all(key)
        return value

    def set_parameter(self, key, new_value):
        param, key, value = self.get_parameter_all(key)
        new_value = param.validator(new_value)
        self.config[key] = new_value
