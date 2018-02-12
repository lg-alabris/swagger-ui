'''
======================================================================
Created on Jan 14, 2018

PURPOSE: this module provides classes to read Maven projects from git or other repos
         specifically intended to create the graph of multiple project dependencies

ROADMAP: TODO - 
        1. review how properties are distributed and could break things
        2. review subproject dependencies on top level, are props declared?
        2. review parent POM, are props declared?
        3. are external property files used?


@author: Larry
======================================================================
'''
import os
import subprocess

#import json
#import xml.etree.ElementTree as ET
#import urllib2
#import csv
import xml.etree.cElementTree as ET
import re
import urllib.request


#=======================================================================   
# static functions and constants
class Util(object):
    mvn_pom_ns = {"mvn":"http://maven.apache.org/POM/4.0.0"}
    
    def __init__(self):
        pass        
        
    @staticmethod
    def get_tag_value(name, section):
        s = ('mvn:%s' % name)
        elem = section.find(s, Util.mvn_pom_ns)
        if elem ==None:
            return''       
        return elem.text

    @staticmethod
    def get_path(dirs):
        path = ''
        for d in dirs:
            path += d + '/'           
        return path[:len(path) -1]

    # if hasattr(a, 'property'):
    
    @staticmethod
    def run_process_2(cmd_args):
        #result = subprocess.run(['dir', '../*.*'], stdout=subprocess.PIPE)
        #result = subprocess.run(['C:/apps/maven352/bin/mvn', 'help:effective-pom'], stdout=subprocess.PIPE)
        result = subprocess.run(['cd', '..'], stdout=subprocess.PIPE, shell=True)        
        result = subprocess.run(cmd_args, stdout=subprocess.PIPE, shell=True)       
        print(result.stdout.decode('utf-8'))

        
    @staticmethod
    def run_process(cmd_args, args_in):
        cmd = subprocess.Popen(cmd_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        if (args_in):
            cmd.stdin.write(args_in.encode('utf-8'))
        cmd.stdin.flush() # Must include this to ensure data is passed to child process
        result = cmd.stdout.read()
        
        print(args_in.encode('utf-8'))
        print(result)  #.stdout.decode('utf-8'))
        '''
        cmdline = ["cmd", "/q", "/k", "echo off"]
        batch = b"""\
        rem vsinstr -coverage helloclass.exe /exclude:std::*
        vsperfcmd /start:coverage /output:run.coverage
        helloclass
        vsperfcmd /shutdown
        exit
        """     
        
        '''
    def test_map_update(self):
        A = {'a':1, 'b':2, 'c': 3}
        B = {'c':99, 'd':4, 'e':5}
        A.update(B)
        print(A)

#=======================================================================   
# identifies Maven coordinates for a project or dependnecy
class MavenCoords(object):
    def __init__(self, element, props):  
        if (not element):
            self.groupid =''
            self.artifactid = ''
            self.version = ''
            self.scope = ''
            self.relative_path = ''
            self.key =''    
            return 
                
        self.groupid = Util.get_tag_value('groupId', element)
        self.artifactid = Util.get_tag_value('artifactId', element)
        self.version = Util.get_tag_value('version', element)   
        self.relative_path = Util.get_tag_value('relativePath', element)   
        self.scope = Util.get_tag_value('scope', element)  
        self.refresh_key(props) 
             
    def refresh_key(self, props):
        if (props and self.version in props):
            self.version = props[self.version]
        self.key = '%s|%s|%s' %  (self.groupid, self.artifactid, self.version)  

       

#=======================================================================   
#  a maven project POM complete with properties and dependencies                       
class MavenProject(object):
    def __init__(self, pom_url, project_map):  
        #dirs = pom_url.split('/')

        self.pom_url = pom_url; 
        self.project_map = project_map
        self.pom_file = self.get_pom_file(self.pom_url)
        self.name = Util.get_tag_value('name',  self.pom_file)   
        self.packaging = Util.get_tag_value('packaging',  self.pom_file)   
 
        self.init_from_parent()         
        self.properties.update(self.get_properties(self.pom_file))                      
        self.coord = MavenCoords(self.pom_file, self.properties)                         
        self.dependencies.update(self.get_dependencies(self.pom_file))
        self.project_map[self.coord.key] = self              
        self.get_sub_modules(self.pom_file)
        self.history = []
        self.consumers = []
        #if self.packaging =='pom':
    
    # parent pom's will always be pre-existent to child pom's. they will be looked by coord key from
    # the global graph / project list 
    def init_from_parent(self):
        parent_section = self.pom_file.findall('mvn:parent', Util.mvn_pom_ns)       
        if (parent_section):
            self.parent_coord = MavenCoords(parent_section[0], None)
            parent = self.project_map[self.parent_coord.key]
            if (parent):
                self.properties = parent.properties.copy()
                self.dependencies = parent.dependencies.copy()               
            else:
                print('Error: POM {} has unresolved parent POM reference {}'.format(self.name, parent.key))   
        else:
            self.dependencies = {}
            self.properties = {} 
            self.coord = MavenCoords(None, None)
        dirs = self.pom_url.split('/')
        print(dirs)
        print (Util.get_path(dirs))
    
    
    def get_sub_modules(self, pom_file):
        section = pom_file.findall('mvn:modules', Util.mvn_pom_ns)       
        self.modules = {}
        if (not section):
            return 
        
        for elem in section[0].findall('*'):
            sub_proj = self.get_sub_module(elem.text)
            self.modules[sub_proj.coord.key] = sub_proj         
            self.project_map[sub_proj.coord.key] = sub_proj
   

    def get_sub_module(self, sub_dir):
        dirs = self.pom_url.split('/')
        x = len(dirs)
        dirs[x-1] = 'pom.xml'
        dirs.insert(x-1, sub_dir)
        path = Util.get_path(dirs)        
        module = MavenProject(path, self.project_map) 
        return module

    def get_properties(self, pom):
        section = pom.findall('mvn:properties', Util.mvn_pom_ns)
        props = {}
        if (len(section)==0):
            return props
        
        for elem in section[0].findall('*'):
            k = re.sub('{.*?}', '', elem.tag)
            k = '${%s}' % k
            props[k] = elem.text
        return props

    def get_dependencies(self, pom):
        section = pom.findall('mvn:dependencies', Util.mvn_pom_ns)
        deps_map = {}
        if (len(section)==0):
            return deps_map
        
        for dep_section in section[0].findall('mvn:dependency', Util.mvn_pom_ns):  
            obj =  MavenCoords(dep_section, self.properties)
            deps_map[obj.key] = obj       
        return deps_map

    @staticmethod
    def get_pom_file(pomfile):
        if pomfile.find("http://") >=0 or pomfile.find("https://") >=0:   
            opener = urllib.request.build_opener()   
            pom = ET.parse( opener.open(pomfile) ).getroot() 
        else:
            pom = ET.parse(pomfile).getroot() 
        return pom

    def logx(self, level):
        print()    
        print('---------Maven Project---------')
        #print('key: %s  *  Group: %s   *  Id: %s   *  Ver: %s' % (self.coord.key, self.coord.groupid, self.coord.artifactid, self.coord.version))
        print('key: {0}  *  Name: {1}  *  Group: {2}   *  Id: {3}   *  Ver: {4}'.format(self.coord.key, self.name, self.coord.groupid, self.coord.artifactid, self.coord.version))
        print() 
        if level ==0:
            return  
        
        print('    dependencies') 
        for k, v in self.dependencies.items():
            print('    key: %s  *  Group: %s   *  Id: %s   *  Ver: %s' % (k, v.groupid, v.artifactid, v.version))
        
        print() 
        print('    properties:  ', self.properties)
        
        print ('    consumers')
        for proj in self.consumers:
            print('    ', proj.coord.key)
 
class DAGerror(Exception):
    def __init__(self, arg):
        self.arg = arg

#=======================================================================   
# 
class MavenProjectGraph(object):
    
    def __init__(self, pom_url_list):
        self.pom_url_list = pom_url_list
        self.proj_list = []
        self.proj_map = {}
        #self.validation = {}
        
    def generate_pom_list(self):
        for pom_url in self.pom_url_list:
            MavenProject(pom_url, self.proj_map)
            #self.proj_list.append(proj)
            #self.proj_map[proj.coord.key] = proj
            
        self.proj_list = list(self.proj_map.values())
        
        for proj in self.proj_list:
            proj.logx(1) #$$
            print()
            
    def set_options(self):
        pass
    
    
    # PURPOSE: sort the list in DAG dependency order and capture each project consumers
    #
    #
    def resolve_graph(self):
        self.resolve_dependencies()
        self.resolve_consumers()
    
    
    # PURPOSE: reorder the project list such that each projects dependencies appear before that project
    #
    # NOTE #1: iterate thru the list looking fwd in the list for each project's dependencies
    #          for each dependency found, move it behind that project
    #
    # NOTE #2: the DAG is complete when the list is scanned and no dependencies exist fwd of each project
    #
    # NOTE #3: a history of each dependency relocation is maintained for each project
    #          a circular reference will be detected if that   
    #         
    def resolve_dependencies(self):
        try:
            while True:
                for p in self.proj_list:
                    print(p.name)

                i = 0          
                #dependency_found = False                    
                while i < len(self.proj_list):
                    dependency_found = False                    
                    proj_base = self.proj_list[i]
                    
                    print('loop i={}, base={}'.format(i, proj_base.name))
                                        
                    j = i + 1
                    while j < len(self.proj_list):
                        print('          loop j {}'.format(j))

                        proj_scan = self.proj_list[j]
                        
                        # a forward project dependency is found for the base project, move it behind the base project
                        if  proj_scan.coord.key in proj_base.dependencies:
                            
                            # dejavu - a repeated reorder indicates circular dependency
                            if proj_scan.coord.key in  proj_base.history:
                                raise DAGerror("Error: base project - {} - encountered duplicate reorder for dependency - {} -".format
                                               ( proj_base.name, proj_scan.name))
                                                                                           
                            # remove the fwd item first to avoid order issues                           
                            del self.proj_list[j]      #self.proj_list.remove(j)
                            
                            # insert behind the base project
                            self.proj_list.insert(i, proj_scan)
                            
                            print('      reorded scan {} from j={} to i={}'.format( proj_scan.name, j, i)) 
                                               
                            for p in self.proj_list:
                                print(p.name)
                            
                            proj_base.history.append(proj_scan.coord.key)                           
                            dependency_found = True
                            i = i -1
                            break
                         
                        j =j+1    # while j
                                              
                    i=i+1         # while i 
                    
                # repeat outer loop until nothing is reordered               
                if not dependency_found:
                    break
                else:
                    i = 0   
                    
        except DAGerror as e:
            print(e)
    
    # PURPOSE: for each project in the list, discover the set of consuming projects
    #
    # NOTE #1: call this method AFTER the dependency graph has been properly resolved
    #          consuming projects will be forward in the list
    #
    def resolve_consumers(self):
        for i in range(len(self.proj_list)):
            proj_base = self.proj_list[i]
            j = i
            while j < len(self.proj_list)-1:
                j = j+1
                proj_scan = self.proj_list[j]
                if (proj_base.coord.key in proj_scan.dependencies):
                    proj_base.consumers.append(proj_scan)
                    
        
    def list_projects(self): 
        for proj in self.proj_list:
            proj.logx(1)   
        
   
#==========================================================================
def main():
    pom_files = ['D:\\devspaces\\wks4\\py1\\snipits2.xml', 
                'https://raw.githubusercontent.com/LeonardoZ/java-concurrency-patterns/master/pom.xml']
    
    pom_files = ['D:\\devspaces\\wks4\\py1\\pom-A.xml', 
                 'D:\\devspaces\\wks4\\py1\\pom-B.xml',
                 'D:\\devspaces\\wks4\\py1\\pom-C.xml',
                 'D:\\devspaces\\wks4\\py1\\pom-D.xml',
                 ]
    
    pom_files = ['C:/Users/Larry/Dropbox/gitcode/gh/maven_proj_graph/pom-A.xml', 
                 'C:/Users/Larry/Dropbox/gitcode/gh/maven_proj_graph/pom-B.xml',
                 'C:/Users/Larry/Dropbox/gitcode/gh/maven_proj_graph/pom-C.xml',
                 'C:/Users/Larry/Dropbox/gitcode/gh/maven_proj_graph/pom-D.xml',
                 ]
    
    # C:\Users\Larry\Dropbox\gitcode\gh\maven_proj_graph
    
    s = ['dir', '*']
    s = ['C:/apps/maven352/bin/mvn', 'help:effective-pom']
    
    s2 = ['C:\\apps\\maven352\\bin\\mvn', 'help:effective-pom']
    
    #Util.run_process(['cd', '..'], 'C:\\apps\\maven352\\bin\\mvn help:effective-pom')
    
    #Util.run_process('C:\\apps\\maven352\\bin\\mvn help:effective-pom', '')
 
    #Util.test_map_update(None)
    
    #return()
        
    graph = MavenProjectGraph(pom_files)
   
    graph.generate_pom_list()
   
    graph.resolve_graph()
    
    graph.list_projects()


#==========================================================================
# see this article for opening remote xml files
# https://stackoverflow.com/questions/28238713/python-xml-parsing-lxml-urllib-request
        
def main2():            
    cwd = os.getcwd()
    cwd = 'D:\\devspaces\\wks4\\py1\\'
    pom_file = cwd + 'snipits2.xml'
    
    pom_file = 'D:\\devspaces\\wks4\\py1\\snipits2.xml'
    pom = ET.parse(pom_file).getroot() 
    
    # https://github.com/LeonardoZ/java-concurrency-patterns.git
    
    # this is the correct patttern for reading single files from github
    # https://raw.githubusercontent.com/user/repository/branch/filename
  
    # this is the web page containing the file     
    # 'https://github.com/LeonardoZ/java-concurrency-patterns/blob/master/pom.xml'
    
    pom_file_url = 'https://raw.githubusercontent.com/LeonardoZ/java-concurrency-patterns/master/pom.xml'
    
    opener = urllib.request.build_opener()
    
    f = opener.open(pom_file_url)
    
    
    # ng, file=urllib.urlopen(file=urllib.urlopen())
       
    #parser = ET.HTMLParser()

    #with urlopen('https://pypi.python.org/simple') as f:
    #tree = ET.parse(f, parser) 

    #pom_file = urllib.request.urlopen(pom_file)
    
    pom = ET.parse(opener.open(pom_file_url)).getroot() 

    project = MavenProject(pom)
    project.logx()

if __name__ == '__main__':
    main()


#main()

'''
=====================================================================
notes:
    alternatives - use maven to get equiv pom 
    >  mvn help:effective-pom

https://stackoverflow.com/questions/4760215/running-shell-command-from-python-and-capturing-the-output


'''

