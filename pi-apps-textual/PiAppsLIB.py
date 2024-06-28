#!/bin/python
import os
import sys
import subprocess
import json

def error(message,code=1):
    print(message)
    quit(code)

def parse_file_in_chunks(file_path, chunk_size=5):
    chunks=[]
    with open(file_path, 'r') as file:
        chunk = []
        for line in file:
            chunk.append(line.strip())
            if len(chunk) == chunk_size:
                chunks.append(chunk)
                chunk = []
        # Process any remaining lines that didn't form a full chunk
        if chunk:
            chunks.append(chunk)
    return chunks

class PiAppsInstance:
    def __init__(self, pi_apps_path):
        self.path=pi_apps_path
        dir_lookup_shell=subprocess.check_output("grep -w '    dir_lookup=' "+os.path.join(self.path,"preload"),shell=True).decode().split("=")
        dir_lookup_shell.pop(0)
        self.dir_lookup=eval("=".join(dir_lookup_shell).replace('( [','{').replace(')','}').replace('[',',').replace(']=',':'))
        #print(self.dir_lookup["All Apps"]) # make sure that dir_lookup was parsed correctly
    def get_structure(self,place=""):
        struc=list()
        apps=[]
        for element in parse_file_in_chunks(os.path.join(self.path,"data","preload","LIST-"+place.replace("/",""))):
            parsed_element={}
            if not element[1]=="Back":
                parsed_element["icons"]={'icon-24': element[0]}
                parsed_element["name"]=element[1]
                parsed_element["value"]=element[2]
                parsed_element["tooltip"]=element[3]
                parsed_element["status_color"]=element[4]
                if not parsed_element["value"].endswith("/"): # defines if it's an app or not
                    parsed_element["type"]="Application"
                    if place=="All Apps/":
                        apps.append(parsed_element["name"])
                else:
                    parsed_element["type"]="Category"
                    parsed_element["content"]=self.get_structure(parsed_element["value"])
                struc.append(parsed_element)
        self.structure=struc
        if place=="All Apps/":
            self.apps=apps
        return struc
    def get_app_details(self,data):
        data["type"]="Application"
        with open(os.path.join(self.path,"apps",data["name"],'description'),'r') as d:
            data["description"]=[ l.replace("\n","") for l in d.readlines()]
        try:
            with open(os.path.join(self.path,"apps",data["name"],'credits'),'r') as c:
                data["credits"]=[ l.replace("\n","") for l in c.readlines()]
        except Exception:
            data["credits"]=[]
        try:
            with open(os.path.join(self.path,"apps",data["name"],'website'),'r') as www:
                data["website"]=www.readline().replace("\n","")
        except Exception:
            data["website"]=""
        if os.path.exists(self.path + "/data/status/" + data["name"]):
            with open(self.path + "/data/status/" + data["name"], 'r') as f_status:
                data["status"]=f_status.readline()[:-1]
        else:
            data["status"]='uninstalled'
        return data
            
instance=PiAppsInstance(os.path.expanduser("~/pi-apps"))