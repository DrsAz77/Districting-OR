#!/usr/bin/env python
# coding: utf-8

# In[1]:


#import all necessary packages
import gurobipy as gp
from gurobipy import GRB
from gerrychain import Graph
import networkx as nx
import geopandas as gpd
import math


# In[3]:


#Set filepath and filename equal to the path/name of the data used respectively
filepath = r'C:\Users\aazizide\OneDrive - Texas Tech University\Desktop\Courses\3- Principles of Operations Research\Project\Districting-OR-main\Districting-OR-main/'
filename= 'AR_county.json'
#Create a new Graph object G from the file
G = Graph.from_json(filepath + filename)


# In[4]:


#Set each node in G to be equal to the population of their respective county
for node in G.nodes:
    G.nodes[node]['TOTPOP'] = G.nodes[node]['P0010001']


# In[6]:


#Print each node, the county it represents, and their 2020 population
for node in G.nodes:
    name = G.nodes[node]['NAME20']
    population = G.nodes[node]['TOTPOP']
    print("Node",node,"represents",name,"County with 2020 population of",population)


# In[7]:


#draw the graph of nodes
nx.draw(G, with_labels=True)


# In[8]:


#set the ceiling and floor of the model equal to the maximum deviation/2 * the average population
dev = 0.01

k = 4
tot_pop = sum(G.nodes[node]['TOTPOP'] for node in G.nodes)

L = math.ceil((1-dev/2)*tot_pop/k)
U = math.floor((1+dev/2)*tot_pop/k)
print("Using L =",L,"and U =",U,"and k =",k)


# In[9]:


#create a new model object and create variables
m = gp.Model()

x = m.addVars(G.nodes, k, vtype=GRB.BINARY)
y = m.addVars(G.edges, vtype=GRB.BINARY)


# In[10]:


#set objective to minimize cut edges
m.setObjective( gp.quicksum( y[u,v] for u,v in G.edges ), GRB.MINIMIZE )


# In[11]:


# each county i is assigned to a district j
m.addConstrs(gp.quicksum(x[i,j] for j in range(k)) == 1 for i in G.nodes)
# each district j has a population at least L and at most U
m.addConstrs( gp.quicksum( G.nodes[i]['TOTPOP'] * x[i,j] for i in G.nodes) >= L for j in range(k))
m.addConstrs( gp.quicksum( G.nodes[i]['TOTPOP'] * x[i,j] for i in G.nodes) <= U for j in range(k))
# an edge is cut if u is assigned to district j but v is not.
m.addConstrs( x[u,j] - x[v,j] <= y[u,v] for u,v in G.edges for j in range(k))
m.update()


# In[12]:


# add root variables: r[i,j] equals 1 if node i is the root of district j
r = m.addVars( G.nodes, k, vtype=GRB.BINARY)

import networkx as nx 

DG = nx.DiGraph(G)

f = m.addVars(DG.edges)


# In[13]:


# The big-M proposed by Hojny et al.
M = G.number_of_nodes() - k + 1
# each district should have one root
m.addConstrs( gp.quicksum( r[i,j] for i in G.nodes ) == 1 for j in range(k) )
# If node i isn't assigned to district j, then it cannot be its root
m.addConstrs( r[i,j] <= x[i,j] for i in G.nodes for j in range(k) )
# If not a root, consume some flow
# If a root, only send out (so much) flow
m.addConstrs( gp.quicksum( f[j,i] - f[i,j] for j in G.neighbors(i) ) 
             >= 1 - M * gp.quicksum( r[i,j] for j in range(k) ) for i in G.nodes )
# Do not send flow across cut edges
m.addConstrs( f[i,j] + f[j,i] <= M * (1-y[i,j] )for i,j in G.edges)

m.update()


# In[17]:


# sole IP model
m.optimize()


# In[18]:


print("The number of cut edges is", m.ObjVal )

# retrieve the districts and their population
districts = [[i for i in G.nodes if x[i,j].x > 0.5] for j in range(k)]
district_counties = [[G.nodes[i]["NAME20"] for i in districts[j] ] for j in range(k)]
district_populations = [sum(G.nodes[i]["TOTPOP"] for i in districts[j]) for j in range(k)]
# print it
for j in range(k):
    print("District",j,"has population",district_populations[j],"and contains counties",district_counties[j])
    print("")


# In[20]:


# Read Oklahoma county shapefile from "OK_county.shp"
filepath = r'C:\Users\aazizide\OneDrive - Texas Tech University\Desktop\Courses\3- Principles of Operations Research\Project\Districting-OR-main\Districting-OR-main/'
filename = 'AR_county.shp'
# Read geopandas dataframe from file
df = gpd.read_file( filepath + filename)


# In[21]:


# Which district is each county assigned to?
assignment = [ -1 for i in G.nodes ]

labeling = { i : j for i in G.nodes for j in range(k) if x[i,j].x > 0.5 }
# add assignments to a column of the dataframe and map it
node_with_this_geoid = { G.nodes[i]['GEOID20'] : i for i in G.nodes }
# pick a position u in the data frame
for u in range(G.number_of_nodes()):
    
    geoid = df['GEOID20'][u]
    i = node_with_this_geoid[geoid]
    assignment[u] = labeling[i]
#print the map    
df['assignment'] = assignment
my_fig = df.plot(column='assignment').get_figure()


# In[ ]:





# In[ ]:





# In[ ]:




