''' 
Tasks (11/10,Fri):
    [DONE] 1) Tidy up plotting code
    [DONE] 2) Test threshold numbers
    [DONE] 3) Turn clusterResp graph into raster plot
'''

#%% Import libraries and packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster
# %matplotlib qt
'''
TODO: Minor
label plots and prep explanations
'''
'''#%% Temp init
tau = 0.1
T = 5000
t = np.arange(0, T, tau)
n = t.shape[0]
time_params = {'tau': tau, 'T': T, 't': t, 'n': n}

n_cells = 10

ibif = 340

# NOTE: fixed input
I = np.random.uniform(ibif, ibif + 1, (n_cells, 1))
I = np.tile(I, n)
ksyn = 2e3


p = 0.2 #fixed probability
w = np.random.uniform(0, 1, (n_cells, n_cells))
w = (w < p).astype(int)
eps = np.random.uniform(0.8, 1.2, (n_cells, n_cells))
k = (ksyn / p) * eps
w = w * k
# t, n, v, g, spike = simulate_network(n_cells, w, I, time_params)

# d_weak = plot_results(t, n, v, g, spike)'''

#%% Define functions
np.random.seed(1)
def simulate_network(n_cells, w, I, time_params):

    tau = time_params['tau']
    T = time_params['T']
    t = time_params['t']
    n = time_params['n']

    A = 1
    t_peak = 2
    psp_amp = 1
    psp_decay = 100

    v = np.zeros((n_cells, n))
    u = np.zeros((n_cells, n))
    g = np.zeros((n_cells, n))
    spike = np.zeros((n_cells, n))
    
    resp_thresh = 5e-4
    # resp_thresh = 4e-4
    clusterResp = np.zeros(n)
    
    # hold onto sum of all presynaptic outputs
    I_net = np.zeros((n_cells, n))

    # neuron parameters
    C = 50
    vr = -80
    vt = -25
    vpeak = 40
    k = 1
    a = 0.01
    b = -20
    c = -55
    d = 150

    # init v and u
    v[:, 0] = vr

    # SIMULATE THE NETWORK IN ORDER TO IDENTIFY THE CLUSTERS
    for i in range(1, n):

        dt = t[i] - t[i - 1]

        # iterate through postsynaptic neurons
        for jj in range(n_cells):

            # iterate through presynaptic neurons
            for kk in range(n_cells):
                if jj != kk:
                    I_net[jj, i - 1] += w[kk, jj] * g[kk, i - 1]

            dvdt = (k * (v[jj, i - 1] - vr) * (v[jj, i - 1] - vt) -
                    u[jj, i - 1] - I_net[jj, i - 1] + I[jj, i - 1]) / C
            dudt = a * (b * (v[jj, i - 1] - vr) - u[jj, i - 1])
            dgdt = (-g[jj, i - 1] + psp_amp * spike[jj, i - 1]) / psp_decay

            v[jj, i] = v[jj, i - 1] + dvdt * dt
            u[jj, i] = u[jj, i - 1] + dudt * dt
            g[jj, i] = g[jj, i - 1] + dgdt * dt

            if v[jj, i] >= vpeak:
                v[jj, i - 1] = vpeak
                v[jj, i] = c
                u[jj, i] = u[jj, i] + d
                spike[jj, i] = 1
                
    # PERFORM THE CLUSTERING
    # get spike times
    spike_times = []
    cmap = ['C0', 'C1', 'C2']
    for i in range(spike.shape[0]):
        spike_times.append(t[spike[i, :] == 1])

    # compute covaraince matrix on output g
    cormat_raw = np.corrcoef(g)

    # k-means cluster cov matrix
    # X = cormat_raw
    # kmeans = KMeans(n_clusters=3).fit(X)
    # cluster_labels = kmeans.labels_

    # Agglomerative cluster cov matrix
    X = cormat_raw
    Z = linkage(X, method='ward', optimal_ordering=True)

    c, coph_dists = cophenet(Z, pdist(X))
    print(c)

    R = dendrogram(
        Z,
        truncate_mode=None,
        no_plot=True,
    )

    k = np.unique(R['color_list']).shape[0]
    clusters = fcluster(Z, k, criterion='maxclust') #request max number of clusters
    cluster_labels = clusters
     
    print("Cluster labels: ", clusters)
    
    clusterResp = np.zeros((np.unique(cluster_labels).shape[0], n))
     
    XX = np.zeros((k, X.shape[1]))
    for i in range(k):
        XX[i, :] = np.array([
            X[clusters == i + 1, :].mean(axis=0),
        ])
    
    # RUN A MODIFIED VERSION OF THE NETWORK THAT RESPONDS CLUSTER SPECIFIC
    for i in range(1, n):

        dt = t[i] - t[i - 1]

        # iterate through postsynaptic neurons
        for jj in range(n_cells):

            # iterate through presynaptic neurons
            for kk in range(n_cells):
                if jj != kk:
                    I_net[jj, i - 1] += w[kk, jj] * g[kk, i - 1]

            dvdt = (k * (v[jj, i - 1] - vr) * (v[jj, i - 1] - vt) -
                    u[jj, i - 1] - I_net[jj, i - 1] + I[jj, i - 1]) / C
            dudt = a * (b * (v[jj, i - 1] - vr) - u[jj, i - 1])
            dgdt = (-g[jj, i - 1] + psp_amp * spike[jj, i - 1]) / psp_decay

            v[jj, i] = v[jj, i - 1] + dvdt * dt
            u[jj, i] = u[jj, i - 1] + dudt * dt
            g[jj, i] = g[jj, i - 1] + dgdt * dt

            if v[jj, i] >= vpeak:
                v[jj, i - 1] = vpeak
                v[jj, i] = c
                u[jj, i] = u[jj, i] + d
                spike[jj, i] = 1
        
        
        # Step 1: compute the average g output per cluster
            # g from each neuron (timestep-by-timestep average)
        
        # Go through each neuron represented in the cluster_labels array
        for icl, cl in enumerate(np.unique(cluster_labels)): # icl = index when cl takes on value; cl = current cluster label
            # print(icl, cl)
            g_mean = g[cluster_labels == cl, i].mean()
            # print(g_mean)
            
            # Step 2: if a cluster's average g output is greater than a threshold, 
            # then record a response for that cluster's response
        
            if g_mean > resp_thresh:
                clusterResp[icl, i] = 1
        
    # Step 3: make a figure that show the time steps that each cluster made a response
    # colour code cluster responses
    # x = time step
    # y = T/F , 1/0s
    
    fig, ax = plt.subplots()
    # for cr in range(clusterResp.shape[0]):    
    for cr, cl in enumerate(np.unique(cluster_labels)):  # cr = index, cl = cluster label
        # Plot the response for each cluster
        ax.plot(t, 
                clusterResp[cr, :], 
                label = f'Cluster {cl}')
    ax.set_title('Responses of each cluster overtime')
    ax.legend()
    plt.show()
    
    # Raster plot    
    spike_times_per_cluster = []
    unique_clusters = np.unique(cluster_labels)
    
    color_palette = sns.color_palette("husl", len(unique_clusters))  # Generates 'len(unique_clusters)' distinct colors
    colors = color_palette[::-1]
    
    for cl in unique_clusters:
        spike_times = t[clusterResp[cl - 1, :] == 1]  # Adjust index if cluster labels start at 1
        spike_times_per_cluster.append(spike_times)
    
    spike_times_per_cluster = spike_times_per_cluster[::-1]
    unique_clusters = unique_clusters[::-1]
    
    fig, ax = plt.subplots()
    ax.eventplot(spike_times_per_cluster, orientation='horizontal', colors=colors, linelengths=0.3)
    ax.set_xlabel('t')
    ax.set_ylabel('Cluster number')
    ax.set_yticks(range(len(unique_clusters)), [f'{int(cl)}' for cl in unique_clusters])
    ax.set_title('Responses of each cluster overtime')
    plt.tight_layout()
    plt.show()
    
    return t, n, v, g, spike

#%%
def plot_results(t, n, v, g, spike):

    # get spike times
    spike_times = []
    cmap = ['C0', 'C1', 'C2']
    for i in range(spike.shape[0]):
        spike_times.append(t[spike[i, :] == 1])

    # compute covaraince matrix on output g
    cormat_raw = np.corrcoef(g)

    # k-means cluster cov matrix
    # X = cormat_raw
    # kmeans = KMeans(n_clusters=3).fit(X)
    # cluster_labels = kmeans.labels_

    # Agglomerative cluster cov matrix
    X = cormat_raw
    Z = linkage(X, method='ward', optimal_ordering=True)

    c, coph_dists = cophenet(Z, pdist(X))
    print(c)

    R = dendrogram(
        Z,
        truncate_mode=None,
        no_plot=True,
    )

    k = np.unique(R['color_list']).shape[0]
    clusters = fcluster(Z, k, criterion='maxclust')
    cluster_labels = clusters
    
    # print("Cluster labels: ", clusters)
    
    XX = np.zeros((k, X.shape[1]))
    for i in range(k):
        XX[i, :] = np.array([
            X[clusters == i + 1, :].mean(axis=0),
        ])

    fig, ax = plt.subplots(2, 1, squeeze=False, figsize=(12, 6))
    im = ax.flatten()[0].imshow(XX, origin='lower', aspect='auto')
    # ax.flatten()[0].set_yticks(np.arange(0, k, 1))
    # ax.flatten()[0].set_xticks(np.arange(0, len(labels), 1))
    # ax.flatten()[0].set_xticklabels(labels)
    R = dendrogram(Z,
                   # truncate_mode='lastp',
                   truncate_mode=None,
                   leaf_rotation=90,
                   leaf_font_size=12,
                   show_contracted=True,
                   ax=ax.flatten()[1])
    plt.suptitle(str(c))
    cbar_ax = fig.add_axes([0.91, 0.55, 0.04, 0.3])
    plt.colorbar(im, cax=cbar_ax)
    plt.show()

    # sort g by k-means clusters and recompute cov matrix
    # NOTE: Seems like I ought to be able to directly sort the cov matrix but I
    # am not quite seeing how at the moment
    sort_inds = np.argsort(cluster_labels)
    g_sort = g[sort_inds, :]
    v_sort = v[sort_inds, :]
    spike_times_sort = [spike_times[i] for i in sort_inds]
    cormat_sort = np.corrcoef(g_sort)

    # plot raster and cov matrix
    fig, ax = plt.subplots(2, 2, squeeze=False)
    ax[0, 0].eventplot(spike_times, colors='k', lineoffsets=1, linelengths=0.75)
    ax[1, 0].eventplot(spike_times_sort,
                       colors='k',
                       lineoffsets=1,
                       linelengths=0.75)
    ax[0, 1].imshow(cormat_raw, origin='lower', aspect='equal')
    ax[1, 1].imshow(cormat_sort, origin='lower', aspect='equal')
    ax[0, 0].set_xlim(0, t.max())
    ax[1, 0].set_xlim(0, t.max())
    plt.show()

    # hold useful data in a data frame for convenience in later steps
    neuron = np.repeat(np.arange(0, n_cells, 1), n)
    cluster = np.repeat(cluster_labels, n)
    d = pd.DataFrame({
        'neuron': neuron,
        'cluster': cluster,
        'g': g.flatten(),
        'v': v.flatten(),
        'spike': spike.flatten(),
        't': np.tile(t, n_cells)
    })
    
    # print(d)
    return d

    dd = d.iloc[::100, :]
    sns.lineplot(data=dd, x='t', y='g', hue='neuron')
    plt.show()
    '''
    plot v and g coloured by cluster
    fig, ax = plt.subplots(n_cells, 2, squeeze=False)
    cmap = ['C0', 'C1', 'C2']
    for i in range(n_cells):
        ax[i, 0].plot(t, v[i, :], color=cmap[cluster_labels[i]])
        ax[i, 1].plot(t, g[i, :], color=cmap[cluster_labels[i]])
    plt.show()

    # figure 5
    fig, ax = plt.subplots(2, 2, squeeze=False)
    cmap = ['C{}'.format(i) for i in range(np.unique(cluster_labels).shape[0])]
    ax[0, 0].eventplot(spike_times_sort,
                       colors=[cmap[x] for x in cluster_labels[sort_inds] - 1],
                       lineoffsets=1,
                       linelengths=0.75)
    dd = d.groupby(['cluster', 't'])['g'].mean().reset_index()
    dd['cluster'] = dd['cluster'].astype('category')
    dd = dd.iloc[::100, :]
    sns.lineplot(data=dd,
                 x='t',
                 y='g',
                 hue='cluster',
                 legend=None,
                 ax=ax[1, 0])
    ax[0, 1].imshow(cormat_sort, origin='lower', aspect='equal')
    gg = g[:, ::100]
    ptm = np.dot(gg.T, gg)
    ax[1, 1].imshow(ptm, origin='lower', aspect='equal')
    ax[0, 0].set_xlim(0, t.max())
    ax[1, 0].set_xlim(0, t.max())
    plt.show()
    '''

#%% init
tau = 0.1
T = 5000
t = np.arange(0, T, tau)
n = t.shape[0]
time_params = {'tau': tau, 'T': T, 't': t, 'n': n}

n_cells = 10

ibif = 340

# NOTE: fixed input
I = np.random.uniform(ibif, ibif + 1, (n_cells, 1))
I = np.tile(I, n)
'''
# for i in range(I.shape[0]):
#     plt.plot(t, I[i, :])
# plt.show()

## NOTE: fluctuating input (changes every 10 ms ~ 10 ms / tau ms / sample)
# I = np.random.uniform(ibif, ibif + 1, (n_cells, int(10 / tau)))
# I = np.repeat(I, n // I.shape[1], axis=1)
# for i in range(I.shape[0]):
#     plt.plot(t, I[i, :])
# plt.show()
'''

ksyn = 2e3

#%% NOTE: weakly interconnected
p = 0.2 #fixed probability
w = np.random.uniform(0, 1, (n_cells, n_cells))
w = (w < p).astype(int)
eps = np.random.uniform(0.8, 1.2, (n_cells, n_cells))
k = (ksyn / p) * eps
w = w * k
t, n, v, g, spike = simulate_network(n_cells, w, I, time_params)

d_weak = plot_results(t, n, v, g, spike)

#%% NOTE: strongly interconnected
p = 0.95
w = np.random.uniform(0, 1, (n_cells, n_cells))
w = (w < p).astype(int)
eps = np.random.uniform(0.8, 1.2, (n_cells, n_cells))
k = (ksyn / p) * eps
w = w * k
t, n, v, g, spike = simulate_network(n_cells, w, I, time_params)

d_strong = plot_results(t, n, v, g, spike)
