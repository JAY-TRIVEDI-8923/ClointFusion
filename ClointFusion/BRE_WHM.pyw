#BOT Recommendation Engine and Work Hour Monitor

import sqlite3
import os
import sys
import datetime
import time
from dateutil import parser
from pathlib import Path
import PySimpleGUI as sg
import traceback
import platform,socket,re,uuid,json,logging
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
from elevate import elevate
import pyinspect as pi
import pyautogui as pg

pi.install_traceback(hide_locals=True,relevant_only=True,enable_prompt=True)

os_name = str(platform.system()).lower()
windows_os = "windows"
linux_os = "linux"
mac_os = "darwin"

if os_name == windows_os:
    clointfusion_directory = r"C:\Users\{}\ClointFusion".format(str(os.getlogin()))
elif os_name == linux_os:
    clointfusion_directory = r"/home/{}/ClointFusion".format(str(os.getlogin()))
elif os_name == mac_os:
    clointfusion_directory = r"/Users/{}/ClointFusion".format(str(os.getlogin()))

img_folder_path =  Path(os.path.join(clointfusion_directory, "Images"))
config_folder_path = Path(os.path.join(clointfusion_directory, "Config_Files"))
cf_splash_png_path = Path(os.path.join(clointfusion_directory,"Logo_Icons","Splash.PNG"))

last_click = ""
COUNTER = 1

# elevate(show_console=False)
try:
    db_file_path = r'{}\BRE_WHM.db'.format(str(config_folder_path))
    
    connct = sqlite3.connect(db_file_path,check_same_thread=False)
    cursr = connct.cursor()
except: #Ask ADMIN Rights if REQUIRED
    if os_name == windows_os:
        elevate(show_console=False)
    else:
        elevate(graphical=False)
    connct = sqlite3.connect(r'{}\BRE_WHM.db'.format(str(config_folder_path)),check_same_thread=False)
    cursr = connct.cursor()

# connct.execute("DROP TABLE SYS_CONFIG")
# connct.execute("DROP TABLE CFEVENTS")

# Creating table
sys_config_table = """ CREATE TABLE IF NOT EXISTS SYS_CONFIG (
            uuid TEXT NOT NULL,
            platform TEXT NULL,
            platform_release TEXT NULL,
            platform_version TEXT NULL,
            architecture TEXT NULL,
            hostname TEXT NULL,
            ip_addr TEXT NULL,
            mac_addr TEXT NULL,
            processor TEXT NULL
        ); """

cursr.execute(sys_config_table)
connct.commit()

try:
    cursr.execute("ALTER TABLE SYS_CONFIG DROP COLUMN RAM")
    connct.commit()
except:
    pass

cursr.execute("Insert into SYS_CONFIG values(?,?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), str(platform.system()), str(platform.release()),str(platform.version()),str(platform.machine()),str(socket.gethostname()),str(socket.gethostbyname(socket.gethostname())),str(':'.join(re.findall('..', '%012x' % uuid.getnode()))),str(platform.processor())))
connct.commit()

event_table = """ CREATE TABLE IF NOT EXISTS CFEVENTS (
            TIME_STAMP TEXT NOT NULL,
            Event_Name TEXT NULL,
            X TEXT NULL,
            Y TEXT NULL,
            KEY TEXT NULL,
            Button_Name TEXT NULL,
            Click_Count TEXT NULL,
            Window_Name TEXT NULL,
            Mouse_RGB TEXT NULL,
            SNIP_File_Path TEXT NULL
            ); """

cursr.execute(event_table)
connct.commit()

def get_time_stamp():
    st = time.time()
    ts = datetime.datetime.fromtimestamp(st).strftime('%Y-%m-%d %H:%M:%S')
    return ts

def get_active_window():
    """
    Get the currently active window.

    Returns
    -------
    string :
        Name of the currently active window.
    """
    
    active_window_name = None
    if sys.platform in ['linux', 'linux2']:
        
        try:
            import wnck
        except ImportError:
            print("wnck not installed")
            wnck = None
        if wnck is not None:
            screen = wnck.screen_get_default()
            screen.force_update()
            window = screen.get_active_window()
            if window is not None:
                pid = window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
        else:
            try:
                from gi.repository import Gtk, Wnck
                gi = "Installed"
            except ImportError:
                print("gi.repository not installed")
                gi = None
            if gi is not None:
                Gtk.init([])  # necessary if not using a Gtk.main() loop
                screen = Wnck.Screen.get_default()
                screen.force_update()  # recommended per Wnck documentation
                active_window = screen.get_active_window()
                pid = active_window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
    elif sys.platform in ['Windows', 'win32', 'cygwin']:
        
        import win32gui
        window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(window)
    elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
        
        from AppKit import NSWorkspace
        active_window_name = (NSWorkspace.sharedWorkspace()
                              .activeApplication()['NSApplicationName'])
    else:
        print("sys.platform={platform} is unknown. Please report."
              .format(platform=sys.platform))
        
    return active_window_name

def on_release(key):
    try:
        try:
            windw=str(get_active_window()) 
        except:
            windw = "unknown"

        windw = str(windw)

        if str(windw).strip() == "" or str(windw).strip() == "Program Manager":
            windw = "Desktop"        
            
        # GRB color below cursor 
        try:
            rgb_pixels = pg.pixel(*pg.position())
        except:
            rgb_pixels = "N/A"

        cursr.execute("Insert into CFEVENTS values(?,?,?,?,?,?,?,?,?,?)", (str(get_time_stamp()),"Key Press",str(pg.position()[0]),str(pg.position()[1]),str(key),"N/A","N/A",str(windw).replace("*",""),str(rgb_pixels), "N/A"))
        connct.commit()
            
    except Exception as ex:
        print("Error in on_press="+str(ex))

def on_press(key):
    pass   

def on_click(x, y, button, pressed):
    global last_click
    global COUNTER
    click_count = 1

    try:
        if pressed:
            pass   
        if not pressed:
            if last_click:
                button_lst = last_click.split("#")
                if str(button) == "Button.left" and button_lst[0] == "Button.left":
                    difference = datetime.datetime.now() - parser.parse(button_lst[1])

                    if difference.microseconds < 200000:
                        click_count = 2

            last_click = str(button) + "#" + str(datetime.datetime.now())

            try:
                windw = str(get_active_window()) 
            except:
                windw = "unknown"

            if str(windw).strip() == "" or str(windw).strip() == "Program Manager":
                windw = "Desktop"

            img=pg.screenshot()

                #GRB color below cursor 
            try:
                rgb_pixels = pg.pixel(x,y)
            except:
                rgb_pixels = "N/A"

                #snip image
            try:
                img=img.crop((x-40,y-40,x+40,y+40))
            except:
                img=img.crop((x-30,y-30,x+30,y+30))

            outputStr = ''.join(e for e in windw if e.isalnum())
            snip_save_path = str(img_folder_path) + "\\" + str(COUNTER) + "-" + str(outputStr) + "-" + str(x) + "_" + str(y) + ".PNG"
            
            try:
                img.save(snip_save_path)
            except:
                pass

            #capture mini-screenshot
            # screenshot_save_path = str(img_folder_path) + str(COUNTER) + "-" + str(windw) + "-" + str(x) + "_" + str(y) + "_SS.png"
            # try:
            #     im = pg.screenshot(screenshot_save_path,region=(pg.position()[0]-150,pg.position()[1]-150,300, 300)) #mini screenshot
            # except:
            #     pass
            try:
                cursr.execute("Insert into CFEVENTS values(?,?,?,?,?,?,?,?,?,?)", (get_time_stamp(),"Mouse Click",str(pg.position()[0]),str(pg.position()[1]),"N/A",str(button),str(click_count),str(windw).replace("*",""),str(rgb_pixels),str(snip_save_path)))
                connct.commit()
            except:
                pass

            COUNTER = COUNTER + 1
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(exc_type)
        print(exc_value)
        print(exc_traceback)
        print("Error in on_click="+str(ex))

def launch_cf_log_generator_gui():      
    keyboard_listener = KeyboardListener(on_release=on_release)
    mouse_listener = MouseListener( on_click=on_click)
        
    try:
        cloint_small_logo_x_base64 = b'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'

        sg.SetOptions(element_padding=(0,0), button_element_size=(10,1), auto_size_buttons=False)      

        layout = [[sg.Text("ClointFusion's Log Generator",font=('Helvetica', 10),text_color='Orange')],
         [sg.Text("..running in background..",text_color='yellow')],
         [sg.Text('', size=(8, 2), font=('Helvetica', 12), justification='center', key='text')],
         [sg.Exit(button_text='Stop',button_color=('white', 'firebrick4'),key='Exit')]]

        window = sg.Window('ClointFusion', layout, no_titlebar=True, auto_size_buttons=False, keep_on_top=True, grab_anywhere=True,element_justification='c',auto_close=False,use_default_focus=True,icon=cloint_small_logo_x_base64)

        current_time = 0
        paused = False
        start_time = int(round(time.time() * 100))
        
        keyboard_listener.start()
        mouse_listener.start()

        while True:      
            # --------- Read and update window --------
            if not paused:
                event, values = window.read(timeout=10)
                current_time = int(round(time.time() * 100)) - start_time

            else:
                event, values = window.read()
            
            if event == sg.WIN_CLOSED or event == 'Exit':        
                try:
                    keyboard_listener.stop()
                    mouse_listener.stop()
                except:
                    pass
                    
                break
                # --------- Display timer in window --------
            window['text'].update('{:02d}:{:02d}'.format((current_time // 100) // 60,
                                                                  (current_time // 100) % 60))
            # window_show_desktop()
                
        window.Close()
    except Exception as ex:
        print("Error in launch_cf_log_generator_gui="+str(ex))

# def pause():
#     # pg.alert("RR")
#     print("PAUSED")

def exit(keyboard_listener,mouse_listener):
    try:
        keyboard_listener.stop()
        mouse_listener.stop()
        os._exit(0) 
        
    except:
        pass

def _getCurrentVersion():
    global c_version
    try:
        if os_name == windows_os:
            c_version = os.popen('pip show ClointFusion | findstr "Version"').read()
        elif os_name == linux_os:
            c_version = os.popen('pip3 show ClointFusion | grep "Version"').read()

        c_version = str(c_version).split(":")[1].strip()
    except:
        pass

    return c_version

def _get_site_packages_path():
    """
    Returns Site-Packages Path
    """
    import subprocess
    try:
        import site  
        site_packages_path = next(p for p in site.getsitepackages() if 'site-packages' in p)
    except:
        site_packages_path = subprocess.run('python -c "import os; print(os.path.join(os.path.dirname(os.__file__), \'site-packages\'))"',capture_output=True, text=True).stdout

    site_packages_path = str(site_packages_path).strip()  
    return str(site_packages_path)

def call_colab_launcher():
    try:
        cmd = "python " + f'{_get_site_packages_path()}' + "\ClointFusion\Colab_Launcher.py"
        os.system(cmd)
    except Exception as ex :
        print("Error in call_dost_client" + str(ex))

def call_dost_client():
    try:
        cmd = "python " + f'{_get_site_packages_path()}' + "\ClointFusion\DOST_HELPER\dost_main.pyw"
        os.system(cmd)
    except Exception as ex :
        print("Error in call_dost_client" + str(ex))

def call_bol():
    try:
        cmd = "python " + f'{_get_site_packages_path()}' + "\ClointFusion\Bol.pyw"
        os.system(cmd)
    except Exception as ex:
        print("Error in call_bol " + str(ex))

def launch_cf_log_generator_gui_new():
    try:
        from pystray import Icon as icon, Menu as menu, MenuItem as item
        from PIL import Image
        import webbrowser

        keyboard_listener = KeyboardListener(on_release=on_release)
        mouse_listener = MouseListener( on_click=on_click)

        keyboard_listener.start()
        mouse_listener.start()

        image = Image.open(cf_splash_png_path)
        
        icon('ClointFusion', image, f"ClointFusion, Made in India with LOVE, version : {_getCurrentVersion()}",menu=menu(
        item(
            'About',
            lambda icon, item: webbrowser.open_new("https://sites.google.com/view/clointfusion-hackathon")),
        item(
            'Colab Launcher',
            lambda icon, item: call_colab_launcher()),           
            # lambda icon, item: webbrowser.open_new("https://colab.research.google.com/github/ClointFusion/ClointFusion/blob/master/ClointFusion_Labs.ipynb")),
        item(
            'Bol (Talk)',
            lambda icon, item: call_bol()),
        item(
            'Dost Client',
            lambda icon, item: call_dost_client()),           
        item(
            'Work Report',
            lambda icon, item: icon.notify("Hi, This is your work hour monitor powered by ClointFusion. Just open a command prompt and type 'work' to view the report")),
        item(
            'Exit',
            lambda icon, item: exit(keyboard_listener,mouse_listener)))).run()

    except Exception as ex:
        print("Error in launch_cf_log_generator_gui_new="+str(ex))            

try:
    launch_cf_log_generator_gui_new()
except Exception as ex:
    pg.alert(ex)