from django.forms import widgets
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template import loader
from django.utils.safestring import mark_safe

class DatetimePickerWidget(widgets.TextInput):
    class Media:
        js = (
            "https://cdn.jsdelivr.net/npm/flatpickr",
            "https://npmcdn.com/flatpickr/dist/l10n/de.js"
        )
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css',)
        }

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        output = super(DatetimePickerWidget, self).render(name, value, final_attrs)
        
        output += '<script>flatpickr("#{id}", {{locale: "de" , enableTime: true, time_24hr: true}});</script>'.format(id=final_attrs.get('id'))
        return output


class ImagePickerWidget(widgets.Widget):
    template_name = 'wunderfest_widgets/image_picker_widget.html'
    
    class Media:
        js = (
            "https://static.filestackapi.com/filestack-js/1.2.1/filestack.min.js",
            static('wunderfest_widgets/js/wunderfest_image_picker.js'),
        )

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

    def render_old(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        output = super(ImagePickerWidget, self).render(name, value, final_attrs)
        output += """<label>{label}</label>
	<img id="{id}_src" src="{value}" style="height:200px;width:auto;"/>
	<button type="button" onclick="openFilepicker('{id}')">Upload</button>""".format(id=final_attrs.get('id'), value=value, label=(final_attrs.get('verbose_name') or name))
        return output
