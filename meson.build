project(
    'pardus-power-manager',
    meson_version: '>= 0.49.0',
    version : '2.0',
    license: ['GplV3']
)

subdir('po')

libexec_dir = '/usr/libexec/'
bin_dir = '/usr/bin/'

pardus_dir = '/usr/share/pardus/power-manager-advanced/'
icons_dir = '/usr/share/icons/hicolor/scalable/status/'
app_icon_dir = '/usr/share/icons/hicolor/scalable/apps/'
udev_dir = '/lib/udev/rules.d'
application_dir = '/usr/share/applications/'
autostart_dir = '/etc/xdg/autostart/'

# install source code
install_subdir('src/client', install_dir: pardus_dir)
install_subdir('src/service', install_dir: pardus_dir)
install_subdir('src/common', install_dir: pardus_dir)
install_subdir('src/udev-trigger', install_dir: pardus_dir)
install_subdir('src/data', install_dir: pardus_dir)
# install icons
foreach icon : ['ppm-performance-button', 'ppm-balanced-button', 'ppm-powersave-button', 
                'pardus-pm-performance-symbolic', 'pardus-pm-powersave-symbolic',
                'pardus-pm-balanced-symbolic']
    install_data('data/'+icon+'.svg', install_dir: icons_dir)
endforeach
install_data('data/pardus-power-manager.svg', install_dir: app_icon_dir)
# install desktop files
install_data('data/ppm-client.desktop', install_dir: application_dir, rename: 'tr.org.pardus.power-manager.desktop')
meson.add_install_script('sh', '-c',
    'ln -s ../share/pardus/power-manager-advanced/client/main.py ' +
    '${DESTDIR}/' + bin_dir + '/pardus-power-manager')
install_data('data/ppm-autostart.desktop', install_dir: autostart_dir)
# install policy file
install_data('src/udev-trigger/ppm.rule', install_dir: udev_dir, rename: '99-ppm.rules')
# install scripts
install_data('data/ppm-libexec.sh', install_dir: libexec_dir, rename: 'pardus-power-manager')
install_data('data/ppm-cli.sh', install_dir: bin_dir, rename: 'ppm')
install_data('data/ppm-trigger.sh', install_dir: libexec_dir, rename: 'ppm-trigger')
if get_option('service') == 'systemd'
    install_data('data/ppm.systemd', install_dir: '/lib/systemd/system/', rename: 'ppm.service')
elif get_option('service') == 'openrc'
    install_data('data/ppm.openrc', install_dir: '/etc/init.d/', rename: 'ppm')
elif get_option('service') == 'sysvinit'
    install_data('data/ppm.sysvinit', install_dir: '/etc/init.d/', rename: 'ppm')
endif
