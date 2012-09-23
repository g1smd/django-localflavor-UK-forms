from django.forms import ValidationError
from django.forms.fields import Field, EMPTY_VALUES
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
import re
import types

class UKPhoneNumberField(Field):
    default_error_messages = {
        'partial': _('Phone number must include an area code.'),
        'non_uk': _('Phone number must be a UK number.'),
        'length_range': _('Phone number must be between %d and %d digits'),
        'length': _('Phone number must be %d digits'),
        'reject_premium': _('Phone number can\'t be a premium rate number.'),
        'reject_service': _('Phone number can\'t be a service number.')
    }
    
    number_specs = (
        (r'^01((1(3[0-48]|[46][0-4]|5[012789]|7[0-49]|8[01349])|21[0-7]|31[0-8]|[459]1\d|61[0-46-9]))\d{6}$',   None,   (4, 3, 4)),
        (r'^016977[23]\d{3}$',                                         None,     (6, 4)),
        (r'^01(3873|5(242|39[456])|697[347]|768[347]|9467)\d{5}$',     None,     (6, 5)),
        (r'^0176888[234678]\d{2}$',                                    None,     (5, 5)),
        (r'^01(2(0(46[1-4]|87[2-9])|545[1-79]|76(2\d|3[1-8]|6[1-6])|9(7(2[0-4]|3[2-5])|8(2[2-8]|7[0-4789]|8[345])))|3(638[2-5]|647[23]|8(47[04-9]|64[015789]))|4(044[1-7]|20(2[23]|8\d)|6(0(30|5[2-57]|6[1-8]|7[2-8])|140)|8(052|87[123]))|5(24(3[2-79]|6\d)|276\d|6(26[06-9]|686))|6(06(4\d|7[4-79])|295[567]|35[34]\d|47(24|61)|59(5[08]|6[67]|74)|955[0-4])|7(26(6[13-9]|7[0-7])|442\d|50(2[0-3]|[3-68]2|76))|8(27[56]\d|37(5[2-5]|8[239])|84(3[2-58]))|9(0(0(6[1-8]|85)|52\d)|3583|4(66[1-8]|9(2[01]|81))|63(23|3[1-4])|9561))\d{3}$',   None,   (5, 5)),
        (r'^01(2(0[024-9]|2[3-9]|3[3-79]|4[1-689]|[58][02-9]|6[0-4789]|7[013-9]|9\d)|3(0\d|[25][02-9]|3[02-579]|[468][0-46-9]|7[1235679]|9[24578])|4(0[03-9]|2[02-5789]|[37]\d|4[02-69]|5[0-8]|[69][0-79]|8[0-5789])|5(0[1235-9]|2[024-9]|3[0145689]|4[02-9]|5[03-9]|6\d|7[0-35-9]|8[0-468]|9[0-5789])|6(0[034689]|2[0-689]|[38][013-9]|4[1-467]|5[0-69]|6[13-9]|7[0-8]|9[0124578])|7(0[0246-9]|2\d|3[023678]|4[03-9]|5[0-46-9]|6[013-9]|7[0-35-9]|8[024-9]|9[02-9])|8(0[35-9]|2[1-5789]|3[02-578]|4[0-578]|5[124-9]|6[2-69]|7\d|8[02-9]|9[02569])|9(0[02-589]|2[02-689]|3[1-5789]|4[2-9]|5[0-579]|6[234789]|7[0124578]|8\d|9[2-57]))\d{6}$',   None,   (5, 6)),
        (r'^02(0[01378]|3[0189]|4[017]|8[0-46-9]|9[012])\d{7}$',       None,     (3, 4, 4)),
        (r'^03[0347]\d{8}$',                                           None,     (4, 3, 4)),
        (r'^0500\d{6}$',                                               None,     (4, 6)),
        (r'^05[56]\d{8}$',                                             None,     (3, 4, 4)),
        (r'^07([1-5789]\d{2}|624)\d{6}$',                              None,     (5, 6)),
        (r'^070\d{8}$',                                               'premium', (3, 4, 4)),
        (r'^08(001111|45464\d)$',                                      None,     (4, 4)),
        (r'^0800\d{6}$',                                               None,     (4, 6)),
        (r'^080[08]\d{7}$',                                            None,     (4, 3, 4)),
        (r'^08(4[2-5]|70)\d{7}$',                                      None,     (4, 3, 4)),
        (r'^0(87[123]|9([01]\d|8[0-3]))\d{7}$',                       'premium', (4, 3, 4)),
        (r'^11[68]',                                                  'service', (3, 3)),
        (r'^999$',                                                    'service', (3,)),
        (r'^1',                                                       'service', None),
    )
    
    def __init__(self, *args, **kwargs):
        self.reject = set(kwargs.pop('reject', ()))
        super(UKPhoneNumberField, self).__init__(*args, **kwargs)
    
    def clean(self, value):
        super(UKPhoneNumberField, self).clean(value)
        
        value = smart_unicode(value)
        
        if value in EMPTY_VALUES:
            return u''
        
        value = re.sub(r'[^0-9+]',        r'',  value)
        value = re.sub(r'(?<!^)\+',       r'',  value)
        value = re.sub(r'^\+44(?=[1-9])', r'0', value)
        value = re.sub(r'^\+44(?=0)',     r'',  value)
        
        if re.match(r'^(\+(?!44)|00)', value):
            raise ValidationError(self.error_messages['non_uk'])
        
        number_spec = self.get_number_spec(value)
        
        if not number_spec:
            raise ValidationError(self.error_messages['partial'])
        
        if number_spec[0] in self.reject:
            raise ValidationError(self.error_messages['reject_%s' % number_spec[0]])
        
        if not self.valid_length(value, number_spec):
            min_length, max_length = self.spec_lengths(number_spec)
            if min_length == max_length:
                raise ValidationError(self.error_messages['length']
                    % min_length)
            else:
                raise ValidationError(self.error_messages['length_range']
                    % (min_length, max_length))
        
        return self.format_number(value, number_spec)
    
    def get_number_spec(self, value):
        for number_spec in self.number_specs:
            if re.match(number_spec[0], value):
                return number_spec[1:]
        return None
    
    def spec_lengths(self, number_spec):
        if not number_spec[1]:
            return None, None
        if type(number_spec[1][-1]) == types.TupleType:
            min_length, max_length = number_spec[1][-1]
            total = sum(number_spec[1][:-1])
            min_length += total
            max_length += total
        else:
            min_length = max_length = sum(number_spec[1])
        return min_length, max_length
    
    def valid_length(self, value, number_spec):
        min_length, max_length = self.spec_lengths(number_spec)
        if min_length is not None and len(value) < min_length: return False
        if max_length is not None and len(value) > max_length: return False
        return True
    
    def format_number(self, value, number_spec):
        if number_spec[1] is None:
            components = (value,)
        else:
            components = []
            position = 0
            last_index = len(number_spec) - 1
            for index, chunk in enumerate(number_spec[1]):
                if index == last_index:
                    components.append(value[position:])
                else:
                    components.append(value[position:position+chunk])
                    position += chunk
        return ' '.join(components)
