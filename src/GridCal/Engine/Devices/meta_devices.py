# This file is part of GridCal.
#
# GridCal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GridCal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GridCal.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np
from typing import List, Dict, AnyStr, Any, Optional
from GridCal.Engine.Devices.types import DeviceType, TimeFrame


class GCProp:

    def __init__(self, units, tpe, definition, profile_name=''):
        """
        GridCal property
        :param units: units of the property
        :param tpe: data type (int, complex, float, etc...)
        :param definition: Definition of the property
        :param profile_name: name of the associated profile property
        """
        self.units = units

        self.tpe = tpe

        self.definition = definition

        self.profile_name = profile_name


class EditableDevice:

    def __init__(self, name, active, device_type: DeviceType,
                 editable_headers: Dict[str, GCProp],
                 non_editable_attributes: List[str],
                 properties_with_profile: Dict[str, Optional[Any]]):
        """
        Class to generalize any editable device
        :param name: Asset's name
        :param active: is active
        :param editable_headers: dictionary of header properties {'magnitude': (unit, type)}
        :param device_type: DeviceType instance
        :param non_editable_attributes: list of non editable magnitudes
        :param properties_with_profile: dictionary of profile properties {'magnitude': profile_magnitude}
        """

        self.name = name

        self.active = active

        self.type_name = device_type.value

        self.device_type = device_type

        # associated graphic object
        self.graphic_obj = None

        self.editable_headers = editable_headers

        self.non_editable_attributes = non_editable_attributes

        self.properties_with_profile = properties_with_profile

    def get_save_data(self):
        """
        Return the data that matches the edit_headers
        :return:
        """

        data = list()
        for name, properties in self.editable_headers.items():
            obj = getattr(self, name)
            if properties.tpe not in [str, float, int, bool]:
                obj = str(obj)
            data.append(obj)
        return data

    def get_headers(self) -> List[AnyStr]:
        """
        Return a list of headers
        """
        return list(self.editable_headers.keys())

    def __str__(self) -> AnyStr:
        """
        Name of the object
        :return: string
        """
        return self.name

    def create_profiles(self, index):
        """
        Create the load object default profiles
        Args:
        :param index: pandas time index
        """
        for magnitude, values in self.properties_with_profile.items():
            self.create_profile(magnitude=magnitude, index=index)

    def resize_profiles(self, index, time_frame: TimeFrame):
        """
        Resize the profiles in this object
        :param index: pandas time index
        :param time_frame: Time frame to use (Short term, Long term)
        """
        n1 = index.shape[0]
        for magnitude, values in self.properties_with_profile.items():
            if values[1] == time_frame:
                # get the current profile
                val = getattr(self, self.properties_with_profile[magnitude]).values[:, 0]
                n2 = val.shape[0]

                if n1 > n2:
                    # extend the values
                    extension = np.ones(n1 - n2, dtype=val.dtype) * getattr(self, magnitude)  # copy the current value
                    val2 = np.r_[val, extension]
                else:
                    # curtail the values
                    val2 = val[:n1]

                # set the profile variable associated with the magnitude
                setattr(self, self.properties_with_profile[magnitude], val2)

    def create_profile(self, magnitude, index, arr=None, arr_in_pu=False):
        """
        Create power profile based on index
        :param magnitude: name of the property
        :param index: pandas time index
        :param arr: array of values to set
        :param arr_in_pu: is the array in per-unit?
        """
        # get the value of the magnitude
        x = getattr(self, magnitude)
        tpe = self.editable_headers[magnitude].tpe
        if arr_in_pu:
            val = arr * x
        else:
            val = np.ones(len(index), dtype=tpe) * x if arr is None else arr

        # set the profile variable associated with the magnitude
        setattr(self, self.properties_with_profile[magnitude], val)

    def ensure_profiles_exist(self, index):
        """
        It might be that when loading the GridCal Model has properties that the file has not.
        Those properties must be initialized as well
        :param index: Time series index (timestamps)
        """
        for magnitude in self.properties_with_profile.keys():

            if index is not None:
                prof_attr = self.properties_with_profile[magnitude]

                df = getattr(self, prof_attr)

                if df is None:
                    # there is no profile, create a new one with the default values
                    # print(self.name, ': created profile for ' + prof_attr)
                    self.create_profile(magnitude=magnitude, index=index)
                else:
                    if df.shape[0] != len(index):
                        # the length of the profile is different from the length of the master profile
                        # print(self.name, ': created profile for ' + prof_attr)
                        self.create_profile(magnitude=magnitude, index=index)
                    else:
                        # all ok
                        pass

            else:
                # warn('The time index is None')
                # self.logger.append('The time index is None')
                pass

    def delete_profiles(self):
        """
        Delete the object profiles (set all to None)
        """
        for magnitude in self.properties_with_profile.keys():
            setattr(self, self.properties_with_profile[magnitude], None)

    def set_profile_values(self, t):
        """
        Set the profile values at t
        :param t: time index (integer)
        """
        for magnitude in self.properties_with_profile.keys():
            profile = getattr(self, self.properties_with_profile[magnitude])
            setattr(self, magnitude, profile[t])

