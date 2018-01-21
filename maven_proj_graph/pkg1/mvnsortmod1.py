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

#import os
#import json
#import xml.etree.ElementTree as ET
#import urllib2
import xml.etree.cElementTree as ET
import re
import urllib.request
import csv

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
    def get_pom(pomfile):
        if pomfile.find("http://") >=0 or pomfile.find("https://") >=0:   
            opener = urllib.request.build_opener()   
            pom = ET.parse( opener.open(pomfile) ).getroot() 
        else:
            pom = ET.parse(pomfile).getroot() 
        return pom
                   

#=======================================================================   
# identifies Maven coordinates for a project or dependnecy
class MavenCoords(object):
    def __init__(self, element, props):        
        self.groupid = Util.get_tag_value('groupId', element)
        self.artifactid = Util.get_tag_value('artifactId', element)
        self.version = Util.get_tag_value('version', element)   
             
        if self.version in props:
            self.version = props[self.version]
        self.key = '%s|%s|%s' %  (self.groupid, self.artifactid, self.version)  
            

#=======================================================================   
#  a maven project POM complete with properties and dependencies                       
class MavenProject(object):
    def __init__(self, pom):  
        self.properties = self.get_properties(pom)        
        self.coord = MavenCoords(pom, self.properties)
        self.dependencies = self.get_dependencies(pom)    
        self.modules = self.get_modules(pom)
        self.packaging = Util.get_tag_value('packaging', pom)   
        self.name = Util.get_tag_value('name', pom)   
        self.history = []
         #if self.packaging =='pom':
    
    def get_modules(self, pom):
        section = pom.findall('mvn:modules', Util.mvn_pom_ns)       
        modules = []
        if (len(section)==0):
            return modules
        
        for e in section[0].findall('*'):
            modules.add(e.text)
        return modules    

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

    def logx(self, level):
        print()    
        print('---------Maven Project---------')
        #print('key: %s  *  Group: %s   *  Id: %s   *  Ver: %s' % (self.coord.key, self.coord.groupid, self.coord.artifactid, self.coord.version))
        print('key: {0}  *  Name: {1}  *  Group: {2}   *  Id: {3}   *  Ver: {4}'.format(self.coord.key, self.name, self.coord.groupid, self.coord.artifactid, self.coord.version))
        print() 
        if level ==0:
            return   
        for k, v in self.dependencies.items():
            print('key: %s  *  Group: %s   *  Id: %s   *  Ver: %s' % (k, v.groupid, v.artifactid, v.version))


class DAGerror(Exception):
    def __init__(self, arg):
        self.arg = arg

#=======================================================================   
# 
class MavenProjectGraph(object):
    def __init__(self, pomlist):
        self.pomlist = pomlist
        self.proj_list = []
        
        for pomfile in self.pomlist:
            proj = MavenProject(Util.get_pom(pomfile))
            self.proj_list.append(proj)
            proj.logx(0)
            print()
             
    def resolve_graph(self):
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
                                                                                           
                            # remove first, avoids order issues                           
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
        
    def list_projects(self): 
        for proj in self.proj_list:
            proj.logx(0)   
        
   
#==========================================================================
def main():
    pom_files = ['D:\\devspaces\\wks4\\py1\\snipits2.xml', 
                'https://raw.githubusercontent.com/LeonardoZ/java-concurrency-patterns/master/pom.xml']
    
    pom_files = ['D:\\devspaces\\wks4\\py1\\pom-A.xml', 
                 'D:\\devspaces\\wks4\\py1\\pom-B.xml',
                 'D:\\devspaces\\wks4\\py1\\pom-C.xml',
                 'D:\\devspaces\\wks4\\py1\\pom-D.xml',
                 ]
    
    
    graph = MavenProjectGraph(pom_files)
   
    graph.resolve_graph()
    
    graph.list_projects()


#==========================================================================
# see this article for opening remote xml files
# https://stackoverflow.com/questions/28238713/python-xml-parsing-lxml-urllib-request
        
def main2():            
    #cwd = os.getcwd()
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



