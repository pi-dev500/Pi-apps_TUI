from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Label, Button, Header, OptionList, DataTable, Input, Static, Markdown, Collapsible, Footer, TabbedContent, Placeholder
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual_terminal import Terminal
import os
import sys
import webbrowser
from PiAppsLIB import PiAppsInstance
self_directory=os.path.dirname(os.path.realpath(sys.argv[0]))
import time
import asyncio
import threading

def write_file(file,text,mode: str ="a"):
    with open(file,mode) as f:
        f.write(text)
def write_file_asynchronously(file,text,mode: str ="a"):
    th=threading.Thread(target=write_file, args=(file,text,mode))
    th.start()
    return th
def X_is_running():
    from subprocess import Popen, PIPE
    p = Popen(["xset", "-q"], stdout=PIPE, stderr=PIPE)
    p.communicate()
    return p.returncode == 0

class AppDisplay(Static):
    queue=[]
    selected_app=None
    piappsMD="""# Pi-Apps
Let's be honest: **Linux is harder to master than Windows.** Sometimes it's not user-friendly, and following an outdated tutorial may break your Raspberry Pi's operating system.  
There is no centralized software repository, except for the `apt` repositories which lack many desktop applications.  
Surely there is a better way! **There is.**  
Introducing Pi-Apps, a well-maintained collection of app installation-scripts that you can run with **one click**.  

Pi-Apps now serves **over 1,000,000 people** and hosts [over 200 apps](https://pi-apps.io/wiki/getting-started/apps-list/)."""
    piappscredits="""The store himself:
Botspot
Theofficialgman
and many others...
For this textual TUI:
pi-dev500
Textualize Team"""
    def __init__(self,lib):
        self.pi_apps_instance=lib
        super().__init__()
    def compose(self):
        with Vertical():
            with VerticalScroll():
                yield Markdown(self.piappsMD,id="APPMD")
                with Collapsible(title="Credits",id='credits_collapsible'):
                    yield Label(self.piappscredits,id="credits")
            with Horizontal(id="actions"):
                yield Button("Install", id="install_button")
                yield Button.error("Uninstall", id="uninstall_button")
    def on_mount(self):
        self.add_class("no_display_app")
    def on_ready(self):
        self.queue_daemon()
    def load_app(self,data):
        self.selected_app=data["name"]
        data=self.pi_apps_instance.get_app_details(data)
        md=self.query_one("#APPMD")
        title="# "+data["name"]
        if data["website"]=="":
            website=""
        else:
            website=f"Website: "+data['website']
        if data["credits"]==[]:
            self.add_class("nocredits")
        else:
            self.remove_class("nocredits")
            self.query_one("#credits").update("\n".join(data["credits"]))
        self.remove_class("no_display_app")
        if data["status"]=="installed":
            self.remove_class("uninstalled_app")
            self.add_class("installed_app")
        elif data["status"]=="uninstalled":
            self.remove_class("installed_app")
            self.add_class("uninstalled_app")
        md.update(title+"\n"+website+"\n"+"\n".join(data["description"]))
    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        if X_is_running():
            webbrowser.open(event.href)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.selected_app:
            match event.button.id:
                case "install_button":
                    action="install-if-not-installed"
                case "uninstall_button":
                    action="uninstall"
                case default:
                    action="check-all"
            self.queue.append(action+";"+self.selected_app)
    @work(exclusive=False)
    async def queue_daemon(self) -> None:
        while True:
            await asyncio.sleep(0.1)
            while len(self.queue)!=0:
                write_file_asynchronously(os.path.join(self.pi_apps_instance.path,"data","manage-daemon","queue"),str(self.queue.pop(0))+"\n")
                
    def revert(self):
        md=self.query_one("#APPMD")
        cre=self.query_one("#credits")
        self.add_class("no_display_app")
        self.remove_class("uninstalled_app")
        self.remove_class("installed_app")
        self.remove_class("nocredits")
        md.update(self.piappsMD)
        cre.update(self.piappscredits)
        self.selected_app=None

class piapps(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),("q","quit","Exit")]
    CSS_PATH="basecss.css"
    
    directory=""
    search=""
    lib=PiAppsInstance(os.path.expanduser("~/pi-apps"))
    structure=lib.get_structure()
    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent("Pi-Apps","Terminal"):
            with Horizontal(id="pagelayout"):
                with Vertical(id="browser"):
                    yield Input(id="search")
                    yield OptionList(*[Option(e,id=e) for e in self.get_page_infos()],id="app_browser")
                self.appframe=AppDisplay(self.lib)
                yield self.appframe
            with VerticalScroll(id="TermLayout"):
                yield Label("The manage log will be shown there:", id="termlabel")
                yield Placeholder("Waiting for terminal..", id="terminal_ph")
        yield Footer()
    def on_mount(self) -> None:
        self.title = "Pi-Apps"
        self.sub_title="Raspberry pi app store for open source projects"
    
    def mount_terminal(self):
        try:
            tph=self.query_one("#terminal_ph")
            tph.remove()
            term=Terminal(os.path.join(self_directory,"terminal-manage")+" "+self.lib.path,id="terminalog")
            self.app.mount(term,after="#termlabel")
            term.start()
        except:
            pass
    def on_ready(self):
        self.mount_terminal()
        self.appframe.on_ready()
    def get_page_infos(self,place="") -> list:
        self.directory_data={}
        for e in self.lib.get_structure(place):
            self.directory_data[e['name']]=e
        if place=="":
            return list(self.directory_data.keys())
        else:
            return ['← Back'] + list(self.directory_data.keys())
    def load_app(self, selected)->None:
        apps=self.lib.get_structure("All Apps")
        for app in apps:
            if app["name"]==selected:
                self.appframe.load_app(app)
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_option = event.option_id
        #with open("l.txt","w") as f: # log file
        #    f.write(str(event.row_key.value))
        ol = self.query_one("#app_browser")
        if selected_option in self.lib.apps:
            self.load_app(selected_option)
            return
        if selected_option=='← Back':
            ol.clear_options()
            if self.directory.endswith("/"):
                self.directory=self.directory[:-1]
            self.directory=os.path.dirname(self.directory)
            if self.directory=="":
                self.sub_title="Raspberry pi app store for open source projects"
            else:
                self.sub_title=self.directory
            page=self.get_page_infos(self.directory)
            ol.add_options([Option(e,id=e) for e in page])
            self.appframe.revert()
        elif self.directory_data[selected_option]["type"]=='Category':
            ol.clear_options()
            self.directory=self.directory_data[selected_option]["value"]
            self.sub_title=self.directory
            page=self.get_page_infos(self.directory_data[selected_option]["value"])
            ol.add_options([Option(e,id=e) for e in page])
            self.appframe.revert()
        else:
            self.load_app(selected_option)
    
    @on(Input.Changed)
    def search_for_app(self, event: Input.Changed):
        self.search=event.value
        ol = self.query_one("#app_browser")
        if not self.search=="":
            apps=self.lib.apps
            keeped_apps=[app for app in apps if self.search.lower() in app.lower()]
            ol.clear_options()
            ol.add_options([Option(e,id=e) for e in keeped_apps])
        else:
            ol.clear_options()
            if self.directory=="":
                self.sub_title="Raspberry pi app store for open source projects"
            else:
                self.sub_title=self.directory
            page=self.get_page_infos(self.directory)
            ol.add_options([Option(e,id=e) for e in page])
            self.appframe.revert()

if __name__ == "__main__":
    app = piapps()
    app.run()