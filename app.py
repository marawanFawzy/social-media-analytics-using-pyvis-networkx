from flask import Flask, render_template, request
from tkinter import *
import networkx as nx
from networkx.algorithms import community, cuts
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
import csv
from pyvis import network as net
from IPython.core.display import HTML
from IPython.display import display
import itertools
from sklearn.metrics.cluster import normalized_mutual_info_score


app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('home.html')


@app.route('/karate')
def get():
    number = request.args.get('number',  type=int)
    # Read nodes from the CSV file
    with open('metadata_primaryschool_Nodes.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader)
        nodes = [(int(row[0]), {'Class': row[1], 'Gender': row[2]})
                 for row in reader]

    # Read edges from the CSV file
    with open('primaryschool_Edges.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)
        edges = [(int(row[0]), int(row[1])) for row in reader]

    # to get nodes and edges fom csv
    # G = nx.Graph()
    # G.add_nodes_from(nodes)
    # G.add_edges_from(edges)

    # create html page with size 500 * 70% with name Zachary’s Karate Club graph and menu and filter
    g4 = net.Network(height='500px', width='70%',
                     select_menu=True,
                     filter_menu=True, neighborhood_highlight=True)

    # dataset karate_club_graph
    G = nx.karate_club_graph()

    # Run the Girvan Newman algorithm
    comp = community.girvan_newman(G)
    # girvan_newman = community.girvan_newman(G)

    k = number-1
    # number of communitis = k+1
    for communities in itertools.islice(comp, k):
        comm = tuple(sorted(c) for c in communities)

    i = 0
    communities = dict()
    for c in comm:
        for j in c:
            communities[j] = i+1
        i = i + 1
    # scale to change the sizes
    scale = 5  # Scaling the size of the nodes by 10*degree
    # tp get degree for each node to dict and * by scale
    d = dict(G.degree)

    # Updating dict
    d.update((x, scale*y) for x, y in d.items())
    # Setting up size attribute to filter on size
    nx.set_node_attributes(G, d, 'size')

    betweenness_centrality = nx.betweenness_centrality(G, None, False, None)
    closeness_centrality = nx.closeness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G)
    pagerank = nx.pagerank(G)

    nx.set_node_attributes(G, betweenness_centrality, 'betweenness_centrality')
    nx.set_node_attributes(G, closeness_centrality, 'closeness_centrality')
    nx.set_node_attributes(G, eigenvector_centrality, 'eigenvector_centrality')
    nx.set_node_attributes(G, communities, 'community')
    nx.set_node_attributes(G, pagerank, 'pagerank')

    # Internal Evaluation
    # Conductance
    # Find the community with the lowest conductance
    min_cond = float('inf')
    min_comm = None

    for c in comm:
        # Calculate the conductance of the community
        cond = cuts.conductance(G, c)
        # Check if this community has lower conductance
        if cond < min_cond:
            min_cond = cond
            min_comm = c

    mod = community.modularity(G, comm)

    # Extract the clustering to be evaluated from the Girvan-Newman output
    clustering = {}
    for node, cluster in communities.items():
        clustering[node] = cluster


    ground_truth = {}
    for node in G.nodes(data=True):
        ground_truth[node[0]] = node[1]["club"]

    # Calculate the NMI score between the two clusterings
    nmi_score = normalized_mutual_info_score(list(ground_truth.values()), list(clustering.values()))

    i = 0
    for node in G.nodes(data=True):
        g4.add_node(node[0], label=str(node[0]), size=node[1]["size"], betweenness_centrality=node[1]["betweenness_centrality"],
                    eigenvector_centrality=node[1]["eigenvector_centrality"],
                    closeness_centrality=node[1]["closeness_centrality"],
                    community=node[1]["community"], pagerank=node[1]["pagerank"])
        i = i+1
    
    g4.from_nx(G)
    g4.show_buttons(filter_=['physics'])
    g4.write_html('karate.html', False, False)

    return render_template('evaluations.html', min_cond=min_cond, min_comm=min_comm, mod=mod , nmi_score=nmi_score)
