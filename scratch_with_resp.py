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
'''
TODO: Minor
label plots and prep explanations

TODO: Major
Add a motor pathway, reward contingencies, and learning.

Seems like a reasonable approach would be for each cluster to be attached to
one motor pathway. But, to pull a single lever or to pull multiple levers?
Maybe start with a single lever that has changing reward contingencies.

What about constant vs fluctuating 'input'? I suppose one natural starting
place would be to start by setting the input to a constant for all cells, but
on a trial-by-trial basis.

The reward contingencies and learning bit seems like a more straightforward
piping over of my old models.
'''


def simulate_network(n_cells, w, I, time_params, w_ctx_msn):

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

    w_alpha = 0.1
    pr_alpha = 0.1
    resp_thresh = 10
    resp_duration = 100
    theta_nmda = 0
    resp = np.zeros(n)
    r_obtained = np.zeros(n)
    r_predicted = np.zeros(n)
    rpe = np.zeros(n)

    for i in range(1, n):

        dt = t[i] - t[i - 1]

        # iterate through postsynaptic neurons
        for jj in range(n_cells):

            # iterate through presynaptic neurons
            for kk in range(n_cells):
                if jj != kk:
                    I_net[jj, i - 1] += w[kk, jj] * g[kk, i - 1]

            dvdt = (k * (v[jj, i - 1] - vr) *
                    (v[jj, i - 1] - vt) - u[jj, i - 1] - I_net[jj, i - 1] +
                    w_ctx_msn[jj, i - 1] * I[jj, i - 1]) / C
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

        # TODO:
        # determine if the lever was pressed or not
        # start by summing all out of the entire network
        # it is possible this architecture will exhibit savings because the mutual
        # inhibition between clusters should / might keep the non-relevant cells
        # pinned down. With no post-synaptic activity, their pre-post weights
        # should remain unchanged.
        if (g[:, i - 1].sum() > resp_thresh) and resp[i - 1] == 0:
            resp[i - 1:i - 1 + resp_duration] = 1

        # TODO: I'm sure I can borrow more elegant structure from the TD-lambda
        # lecture
        r_obtained[i - 1] = 1 if resp[i] == 1 else 0
        rpe[i - 1] = r_predicted[i - 1] - r_obtained[i - 1]
        r_predicted[i:] = r_predicted[i - 1] + pr_alpha * rpe[i - 1]

        # TODO: I think I can move the response / reward stuff to the top of
        # the function and then only iterate through the nested for loops
        # once... though it might be a bit counter-intuitive to read...

        # TODO: update ctx-str weights
        for jj in range(n_cells):  # post
            for kk in range(n_cells):  # pre
                if jj != kk:

                    pre = g[kk, i - 1]
                    post = np.clip(g[jj, i - 1] - theta_nmda, 0, None)
                    w_ctx_msn[kk, jj] += w_alpha * pre * post * rpe[i - 1]

        # TODO: every time a response happens a little spike of reward is
        # delivered, and the system updates its weights. As it is programmed
        # now, the update in weights happens instantaneously. I suppose that
        # may be a reasonable place to start. Moving forward, we probably want
        # the weight update to take some time, and so to be governed by it's
        # own differential equations / signalling cascade etc. I've done this
        # somewhere (probably the TD spiking IC project).

    return t, n, v, g, spike, w_ctx_msn, resp, r_obtained, r_predicted, rpe


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
    Z = linkage(X, method='ward')

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
                   truncate_mode='lastp',
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
    ax[0, 0].eventplot(spike_times, colors='k', lineoffsets=1, linelengths=0.1)
    ax[1, 0].eventplot(spike_times_sort,
                       colors='k',
                       lineoffsets=1,
                       linelengths=0.1)
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
        'spike': spike.flatten(),
        't': np.tile(t, n_cells)
    })
    # dd = d.iloc[::100, :]
    # sns.lineplot(data=dd, x='t', y='g', hue='neuron')
    # plt.show()

    # # plot v and g coloured by cluster
    # fig, ax = plt.subplots(n_cells, 2, squeeze=False)
    # cmap = ['C0', 'C1', 'C2']
    # for i in range(n_cells):
    #     ax[i, 0].plot(t, v[i, :], color=cmap[cluster_labels[i]])
    #     ax[i, 1].plot(t, g[i, :], color=cmap[cluster_labels[i]])
    # plt.show()

    # figure 5
    fig, ax = plt.subplots(2, 2, squeeze=False)
    cmap = ['C{}'.format(i) for i in range(np.unique(cluster_labels).shape[0])]
    ax[0, 0].eventplot(spike_times_sort,
                       colors=[cmap[x] for x in cluster_labels[sort_inds] - 1],
                       lineoffsets=1,
                       linelengths=0.1)
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


tau = 0.1
T = 1000
t = np.arange(0, T, tau)
n = t.shape[0]
time_params = {'tau': tau, 'T': T, 't': t, 'n': n}

n_cells = 5

# NOTE: Input --- off for 1s, on for 1s, off for 1s
ibif = 325
II = np.hstack((np.zeros((n_cells, int(
    (T // 3) / tau))), np.ones((n_cells, int(
        (T // 3) / tau))), np.zeros((n_cells, int((T // 3) / tau)))))
II = np.tile(II, n // II.shape[1])
I = np.zeros((n_cells, t.shape[0]))
I[:, 0:II.shape[1]] = II
for i in range(I.shape[0]):
    plt.plot(t, I[i, :])
plt.show()

w_ctx_msn = np.random.normal(1, 0.1, I.shape)

# NOTE: weakly interconnected
p = 0.15

# NOTE: strongly interconnected
# p = 0.85

k = 1e-4
w = np.random.uniform(0, 1, (n_cells, n_cells))
w = (w < p).astype(int)
w = 0
eps = np.random.uniform(0.8, 1.2, (n_cells, n_cells))
w = (k / p) * eps

t, n, v, g, spike, w_ctx_msn, resp, r_obtained, r_predicted, rpe = simulate_network(
    n_cells, w, I, time_params, w_ctx_msn)
# plot_results(t, n, v, g, spike)
