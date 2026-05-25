## **Earth Mover’s Distance based Similarity Search at Scale** 

Yu Tang _[†]_ , Leong Hou U _[‡]_ , Yilun Cai _[†]_ , Nikos Mamoulis _[†]_ , Reynold Cheng _[†]_ 

> _†_ The University of Hong Kong _‡_ University of Macau 

> _†{_ ytang, ylcai, nikos, ckcheng _}_ @cs.hku.hk _‡_ ryanlhu@umac.mo 

## **ABSTRACT** 

Earth Mover’s Distance (EMD), as a similarity measure, has received a lot of attention in the fields of multimedia and probabilistic databases, computer vision, image retrieval, machine learning, etc. EMD on multidimensional histograms provides better distinguishability between the objects approximated by the histograms (e.g., images), compared to classic measures like Euclidean distance. Despite its usefulness, EMD has a high computational cost; therefore, a number of effective filtering methods have been proposed, to reduce the pairs of histograms for which the exact EMD has to be computed, during similarity search. Still, EMD calculations in the refinement step remain the bottleneck of the whole similarity search process. In this paper, we focus on optimizing the refinement phase of EMD-based similarity search by (i) adapting an efficient min-cost flow algorithm (SIA) for EMD computation, (ii) proposing a dynamic distance bound, which can be used to terminate an EMD refinement early, and (iii) proposing a dynamic refinement order for the candidates which, paired with a concurrent EMD refinement strategy, reduces the amount of needless computations. Our proposed techniques are orthogonal to and can be easily integrated with the state-of-the-art filtering techniques, reducing the cost of EMD-based similarity queries by orders of magnitude. 

## **1. INTRODUCTION** 

Given two histograms (e.g., probability distributions), their _Earth Mover’s Distance_ (EMD) is defined as the minimum amount of work to transform one histogram into the other. EMD is robust to outliers and small shifts of values among histogram bins [20], improving the quality of similarity search in different domain areas, such as computer vision [19, 21], machine learning [6, 9], information retrieval [23, 24], probabilistic [25, 32] and multimedia databases [5, 30]. Typically, the EMD between two histograms is modeled and solved as a linear optimization problem, the _min-cost flow problem_ , which requires super-cubic time. The high computational cost of EMD restricts its applicability to datasets of lowscale. For example, in computer vision applications, the quality of results is typically compromised by the use of low-granularity histograms, to render EMD-based similarity retrieval feasible [22,30]. 

This work is licensed under the Creative Commons AttributionNonCommercial-NoDerivs 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-nd/3.0/. Obtain permission prior to any use beyond those covered by the license. Contact copyright holder by emailing info@vldb.org. Articles from this volume were invited to present their results at the 40th International Conference on Very Large Data Bases, September 1st - 5th 2014, Hangzhou, China. _Proceedings of the VLDB Endowment,_ Vol. 7, No. 4 Copyright 2013 VLDB Endowment 2150-8097/13/12. 

EMD-based similarity search has been extensively studied in [5, 25,30,32]. Given a query histogram **q** and a database of histogram objects _D_ , the objective is to find the _k_ nearest neighbors of **q** in _D_ . All these works adopt the _filter-and-refinement_ framework; to evaluate a query, unpromising objects (or object groups) are filtered out, by utilizing various effective EMD lower bound estimations, based on centroids and projections [7], dimensionality reduction [30], primal-dual space [32], normal distributions [25], etc. Actual EMD calculations[1] are applied only between **q** and all objects that survive the filter step. Thus, the primary focus of previous research has been in tightening the lower bounds such that more objects can be pruned at the filter step. For instance, [25] demonstrate that the projection-based lower bound can be up to 90% of the actual EMD. However, the effectiveness of a lower bound largely depends on various factors, such as the dimensionality and granularity of histograms, the data distribution, and the parameters of the similarity query (e.g., _k_ ). In particular, for large-scale datasets (e.g., 1M cardinality and/or 1K histogram dimensionality), the current state-of-the-art solution [25] is not feasible, due to the extreme cost of the refinement step. For instance, based on the experiments in [25], it may take 10 minutes[2] to complete one _k_ -NN query on a dataset with 1M objects even when 99% of objects are filtered out. 

In view of this, we focus on optimizing the _refinement phase_ of EMD-based similarity search. Calculating the EMD between two object histograms is equivalent to finding the _minimum-cost flow_ (MCF) in a bipartite network, where each vertex indicates a histogram bin and edges connect bins from different object histograms. Techniques from operations research [1], such as network simplex, primal-dual, successive shortest path, and cost-scaling can be used to solve MCF. However, these solutions do not scale well with the number of histogram bins since their computations rely on a complete bipartite network. For example, consider two histograms having 1K bins each, and the corresponding flow graph (bipartite network) with 1M (1K _×_ 1K) edges in total. Constructing and using this graph for solving MCF requires high computational resources. To alleviate this problem, we adapt a _simplified graph incremental algorithm_ (SIA), originally proposed for assignmentjoins in spatial databases [29], which incrementally constructs the flow graph during the flow calculations based on the edge weights. Our adaptation significantly reduces the EMD computation time. 

Min-cost flow algorithms, such as SIA, only aim at efficiently evaluating a single EMD computation but they do not exploit the execution plan of EMD-based similarity queries. In other words, by integrating SIA into the filter-and-refinement framework as a black-box module, the number of EMD calculations is not affected, 

> 1By _EMD calculation_ we refer to the entire run of an algorithmic process that computes the EMD between two histograms. 

> 2A linear estimation derived from the IRMA experiment in [25]. 

313 

and every calculation is still conducted at its _entirety_ . In our study, we observe that it is possible to incrementally derive and tighten a _running lower bound_ for the EMD during the SIA calculation. Based on this, we introduce a _progressive bounding_ (PB) technique, which can terminate the SIA calculations early for histograms that are no longer promising to the similarity query. In addition, we propose a _dynamic refinement ordering_ (DRO) technique, which concurrently handles and dynamically re-orders multiple EMD calculations. These two techniques greatly reduce the computations at the refinement phase of EMD-based similarity search, boosting the search performance. 

PB and DRO can be seamlessly integrated with any existing (and future) filtering techniques. We show by experimentation that our techniques can compute EMD-based similarity queries one to two orders of magnitude faster, compared to the current state-of-theart [25]. To the best of our knowledge, ours is the first study on this subject that considers datasets of million-scale on the object cardinality and thousand-scale on the histogram dimensionality. 

The rest of the paper is organized as follows. Section 2 formally defines EMD, presents a min-cost flow algorithm for its computation, and discusses the standard filter-and-refinement framework used for EMD-based similarity queries. Section 3 describes SIA, an optimized implementation of the successive shortest path MCF algorithm. Section 4 presents our progressive bounding and dynamic refinement ordering techniques. Section 5 includes an extensive experimental evaluation which demonstrates the effectiveness of our techniques. Related work is presented in Section 6. Finally, Section 7 concludes the paper with a discussion about future work. 

## **2. PRELIMINARIES** 

The _Earth Mover’s Distance_ (EMD), first introduced by the computer vision community in [23,24], is a distance function that measures the dissimilarity of two histograms (e.g., probability or feature distributions). Given two histograms **q** = ( _q_ 1 _, . . . , qn_ ) and **p** = ( _p_ 1 _, . . . , pn_ ), each having _n_ bins, a _flow matrix_ **F** , where _fi,j_ indicates flow (i.e., earth) to move from _qi_ to _pj_ , and a _cost matrix_ **C** , where _ci,j_ models cost of moving flow from the _i_ -th bin to the _j_ -th bin, we can define the total cost of moving unit flow according to **F** and **C** between **q** and **p** as 

_emd_ ( **q** _,_ **p** ) is the minimum cost needed to transform **q** to **p** ; to do so, we distribute the flow (i.e., earth) from each bin _qi_ to a set of initially empty bins for **p** , such that the resulting histogram will be equal to **p** . As moving earth _fi,j_ from _qi_ to the _j_ -th bin of **p** bears a cost _fi,jci,j_ , the objective is to find the flow distribution that results in the minimum total cost. Note that _emd_ ( **q** _,_ **p** ) is equal to _emd_ ( **p** _,_ **q** ) when the cost matrix **C** is symmetric. 

We demonstrate the calculation and applicability of EMD via a real example from web data analysis. Figure 1(a) and 1(b) illustrate the download rates of four music genres by two customers, **q** and **p** , in an online store. The rates are normalized such that all values of each histogram sum to 10. To calculate the distance _emd_ ( **q** _,_ **p** ) between the two customers, we should identify the minimum work to transform genre distribution **q** to distribution **p** . Assume that the cost matrix **C** of the music genres is as shown in Table 1, where indices 1, 2, 3, 4 denote the four music genres (i.e., _R&B_ , _Samba_ , _Jazz_ , and _House_ , respectively). Figure 1(c) illustrates the best transformation of **q** to **p** in terms of the total cost among all feasible transformations. For instance, there are 3 units in **q** ’s _R&B_ genre. In the transformation, _f_ 1 _,_ 1 = 2 units are moved to **p** ’s _R&B_ (with cost 2 _· c_ 1 _,_ 1 = 0) and _f_ 1 _,_ 3 = 1 unit is moved to **p** ’s _Jazz_ (with cost 1 _· c_ 1 _,_ 3 = 0 _._ 1). Thus, based on the best transformation, _emd_ ( **q** _,_ **p** ) is 0 _._ 1+2 _._ 4+0+0 = 2 _._ 5, providing a quantitative measure for the dissimilarity between these two customers. This example demonstrates an application of EMD to viral marketing analysis, which enables enterprises to derive similarities between customers in order to promote their products. 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0002-07.png'>
The image contains three bar charts labeled (a), (b), and (c). Each chart shows download rates for four music genres: R&B, Samba, Jazz, and House. The y-axis is labeled "Download rates" and the x-axis lists the music genres.

### Chart (a): q's distribution
- **R&B**: Two bars, one with a value of 3 and the other with a value of 4.
- **Samba**: Two bars, one with a value of 2 and the other with a value of 4.
- **Jazz**: Two bars, one with a value of 3 and the other with a value of 4.
- **House**: Two bars, one with a value of 1 and the other with a value of 4.

### Chart (b): p's distribution
- **R&B**: Two bars, one with a value of 2 and the other with a value of 4.
- **Samba**: Two bars, one with a value of 1 and the other with a value of 4.
- **Jazz**: Two bars, one with a value of 4 and the other with a value of 4.
- **House**: Two bars, one with a value of 3 and the other with a value of 4.

### Chart (c): emd(q, p)
- **R&B**: Two bars, one with a value of 2 and the other with a value of 4.
- **Samba**: Two bars, one with a value of 1 and the other with a value of 4.
- **Jazz**: Two bars, one with a value of 4 and the other with a value of 4.
- **House**: Two bars, one with a value of 3 and the other with a value of 4.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
4 4<br>3 3<br>2 2<br>1 1<br>(a) q ’s distribution (b) p ’s distribution (c) emd ( q ,  p )<br>R&BSambaJazzHouse R&BSambaJazzHouse R&BSambaJazzHouse<br>Download rates Download rates Download rates<br>**----- End of picture text -----**<br>


**Figure 1: A concrete example of online music library analysis** 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0002-09.png'>
The image contains a mathematical equation:

\[ d(\mathbf{q}, \mathbf{p}) = \sum_{i=1}^{n} \sum_{j=1}^{n} f_{i,j} c_{i,j} \]

This is labeled as equation (1).
</IMAGE_CONTEXT>




The cost matrix (a.k.a., ground distance) **C** can be designed by domain experts and/or derived from a mathematical formula [25, 32]. Intuitively, _ci,i_ = 0 and the larger the distance between _i_ and _j_ in the bin space, the larger _ci,j_ is.[3] Assuming that **q** and **p** are _normalized_ such that[�] _[n] i_ =1 _[q][i]_[=][�] _[n] i_ =1 _[p][i]_[,][the][EMD][between] **[q]** and **p** is formally defined as follows: 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0002-11.png'>
The image contains a mathematical expression:

\[ \text{emd}(\mathbf{q}, \mathbf{p}) = \min_{\mathbf{F}} d(\mathbf{q}, \mathbf{p}), \]

such that

\[ \forall i, j \in [1, n] : f_{i,j} \geq 0, \]
\[ \forall i \in [1, n] : \sum_{j=1}^{n} f_{i,j} = q_i, \]
and
\[ \forall j \in [1, n] : \sum_{i=1}^{n} f_{i,j} = p_j \]

(2)
</IMAGE_CONTEXT>




3The motivating example of [32] partitions a 2-dimensional feature space (humidity and temperature) into 4 _×_ 4 cells based on the range of domain values. The cost _ci,j_ between bins _i_ and _j_ is represented by their Euclidean distance of the corresponding cells. 

**Table 1: Cost matrix C of 4 music genres** 

|_p_1|_p_2|_p_3|_p_4|
|---|---|---|---|
|0|0.9|0.1|0.7|
|0.9|0|0.6|0.9|
|0.1|0.6|0|0.3|
|0.7|0.9|0.3|0|






<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0002-15.png'>
The image contains three diagrams labeled (a), (b), and (c). Each diagram represents a network flow problem with nodes and directed edges.

### Diagram (a): Flow graph

This diagram shows a bipartite graph with two sets of nodes: q and p. The nodes are connected by directed edges with capacities indicated on each edge. The nodes are numbered as follows:

- Set q: q₁, q₂, q₃, q₄
- Set p: p₁, p₂, p₃, p₄

The capacities on the edges are as follows:
- From q₁ to p₁: 3
- From q₁ to p₂: 4
- From q₁ to p₃: 2
- From q₁ to p₄: 1
- From q₂ to p₁: 0
- From q₂ to p₂: 1
- From q₂ to p₃: 4
- From q₂ to p₄: 2
- From q₃ to p₁: 0
- From q₃ to p₂: 0
- From q₃ to p₃: 2
- From q₃ to p₄: 3
- From q₄ to p₁: 0
- From q₄ to p₂: 0
- From q₄ to p₃: 0
- From q₄ to p₄: 1

### Diagram (b): Min-cost flow

This diagram also shows a bipartite graph similar to diagram (a) but includes additional information about the flow and cost on each edge. The format for the labels on the edges is "flow/capacity". The flows and capacities are as follows:

- From q₁ to p₁: 2/2
- From q₁ to p₂: 1/3
- From q₁ to p₃: 2/2
- From q₁ to p₄: 0/1
- From q₂ to p₁: 0/0
- From q₂ to p₂: 1/1
- From q₂ to p₃: 2/3
- From q₂ to p₄: 1/2
- From q₃ to p₁: 0/0
- From q₃ to p₂: 0/0
- From q₃ to p₃: 2/2
- From q₃ to p₄: 1/3
- From q₄ to p₁: 0/0
- From q₄ to p₂: 0/0
- From q₄ to p₃: 0/0
- From q₄ to p₄: 1/1

### Diagram (c): Feasible path

This diagram shows a feasible path in the network. It highlights a specific path from q₃ to p₄ through intermediate nodes. The edges along this path are marked with dashed lines. The flows and capacities on the edges are as follows:

- From q₁ to p₁: 2/2
- From q₁ to p₂: 1/3
- From q₁ to p₃: 2/2
- From q₁ to p₄: 0/1
- From q₂ to p₁: 0/0
- From q₂ to p₂: 1/1
- From q₂ to p₃: 2/3
- From q₂ to p₄: 1/2
- From q₃ to p₁: 0/0
- From q₃ to p₂: 0/0
- From q₃ to p₃: 2/2
- From q₃ to p₄: 1/3
- From q₄ to p₁: 0/0
- From q₄ to p₂: 0/0
- From q₄ to p₃: 0/0
- From q₄ to p₄: 1/1

The feasible path is highlighted with dashed lines connecting q₃ to p₄ through intermediate nodes.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
q p q p q p<br>3 q1 p1 2 0 q1 2/2 p1 0 1 q1 2/2 p1 0<br>1/3 0/3<br>4 q2 p2 1 0 q2 1/1 p2 0 0 q2 1/1 p2 0<br>2/31/4 1/3 2/4<br>2 q3 p3 4 0 q3 2/2 p3 0 0 q3 2/2 p3 0<br>1 q4 p4 3 0 q4 1/1 p4 0 0 q4 1/1 p4 1<br>(a) Flow graph (b) Min-cost flow (c) Feasible path<br>**----- End of picture text -----**<br>


**Figure 2: The flow network of the music example** 

314 

## **2.1 Computing the EMD** 

EMD can be computed using linear programming [12] and network flow algorithms [1]. We now explain how EMD computation can be modeled and solved as a network flow problem. We first construct a bipartite flow network (see Figure 2(a) for the example of Figure 1), where the vertices are derived from the histogram bins (e.g., music genres) and the edges connect the bins between the two histograms. Each edge carries a cost according to the corresponding cell of the cost matrix. The _flow capacity_ of each vertex corresponds to the value of the corresponding histogram bin. For instance, the flow capacity of vertex _q_ 1 (i.e., _R&B_ of **q** ) in Figure 2(a) is set to 3 according to Figure 1(a). Finding the _minimum-cost flow_ in this bipartite graph is equivalent to finding the EMD from **q** to **p** . Each vertex of **q** should send total flow equal to its capacity and each vertex of **p** should receive total flow equal to its capacity. The minimum-cost flow is shown in Figure 2(b). On each edge _e_ ( _qi, pj_ ), the label _fi,j/capi,j_ shows the flow _fi,j_ sent from the origin vertex _qi_ and the _capacity capi,j_ of that edge (i.e., the maximum flow which could possibly be sent from _qi_ to _pj_ ). The edge capacity _capi,j_ is the minimum capacity of the two end-vertices; e.g., the capacity of _e_ ( _q_ 2 _, p_ 4) is 3 (= min _{capq_ 2 _, capp_ 4 _}_ = min _{_ 4 _,_ 3 _}_ ). 

The _successive shortest path_ (SSP) algorithm [1] is the most representative algorithm in the category of the network flow based solutions. SSP iteratively computes and _augments_ paths that (i) start from a vertex _qi_ which has remaining flow capacity, (ii) terminate to a vertex _pi_ which also has remaining flow capacity, and (iii) nodes from **q** and **p** are alternated in these paths. A valid path should include _feasible_ edges only. Given a flow graph, an edge is _feasible_ if there is remaining flow capacity on the edge. When augmenting a flow _fi,j_ on an edge _e_ ( _qi, pj_ ), we subtract _fi,j_ from the capacity of _e_ ( _qi, pj_ ) and add _fi,j_ to the flow capacity of _e_ ( _pj, qi_ ). In our running example, initially, no flow has been augmented on any edge (i.e., the _fi,j_ labels of all edges are set to 0); thus, edge _e_ ( _q_ 2 _, p_ 4) (illustrated in Figure 3(a)) is feasible since the remaining flow capacity from _q_ 2 to _p_ 4 is 3 (illustrated by the number on the dashed line). If we augment 1 unit of flow on _e_ ( _q_ 2 _, p_ 4), we subtract 1 from the capacity of _e_ ( _q_ 2 _, p_ 4) and add 1 to the capacity of _e_ ( _p_ 4 _, q_ 2) (as shown in Figure 3(b)). Note that _e_ ( _p_ 4 _, q_ 2) is not a physical edge in _G_ , as there are only directed edges from **q** to **p** but not viceversa. However, during path computation, SSP traverses also reverse edges provided that they are feasible. A formal definition of feasible edges is given below. The capacity of a non-physical edge (i.e., reverse edge) _e_ ( _pj, qi_ ) always equals to the flow _fi,j_ currently on edge _e_ ( _qi, pj_ ). 

DEFINITION 1 (FEASIBLE EDGE). _Given a flow graph, a physical edge e_ ( _qi, pj_ ) _is feasible if fi,j < capi,j; a non-physical (reverse) edge e_ ( _pj, qi_ ) _is feasible if fi,j >_ 0 _._ 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0003-04.png'>
The image contains two diagrams labeled (a) and (b), each depicting a flow between two nodes labeled \( q \) and \( p \). The nodes have subscripts indicating their respective states: \( q_2 \) and \( p_4 \).

### Diagram (a): Before augmentation

- **Nodes**: 
  - \( q_2 \) with a subscript "4" below it.
  - \( p_4 \) with a subscript "3" below it.
  
- **Flow**:
  - An arrow from \( q_2 \) to \( p_4 \) labeled "3".
  - A reverse arrow from \( p_4 \) to \( q_2 \) labeled "0/3".

### Diagram (b): After augmentation

- **Nodes**:
  - \( q_2 \) with a subscript "3" below it.
  - \( p_4 \) with a subscript "2" below it.
  
- **Flow**:
  - An arrow from \( q_2 \) to \( p_4 \) labeled "2".
  - A reverse arrow from \( p_4 \) to \( q_2 \) labeled "1/3".
</IMAGE_CONTEXT>




**Figure 3: Augmenting 1 flow on edge** _e_ ( _qs, ph_ ) 

Besides, the _cost cf_ ( _u, v_ ) of an edge _e_ ( _u, v_ ) is determined by its physical existence in the flow graph and the cost matrix **C** : 

DEFINITION 2 (COST OF FEASIBLE EDGE). _The cost of a physical edge e_ ( _qi, pj_ ) _is cf_ ( _qi, pj_ ) = _ci,j, while the cost of a non-physical (reverse) edge e_ ( _pj, qi_ ) _is cf_ ( _pj, qi_ ) = _−ci,j._ 

For instance, the reverse edge _e_ ( _p_ 4 _, q_ 2) in Figure 3(b) is feasible. Its cost is _cf_ ( _p_ 4 _, q_ 2) = _−c_ 2 _,_ 4 = _−_ 0 _._ 9 since _e_ ( _p_ 4 _, q_ 2) is not a physical edge. To calculate the min-cost flow (i.e., EMD), SSP iteratively searches for the _feasible_ path having the _minimum cost_ . As discussed above, a feasible path starts from a vertex in **q** , which still has positive flow capacity, ends at a vertex in **p** with positive flow capacity and includes only feasible edges. For instance, there is a feasible path highlighted by three dashed lines in Figure 2(c); the path starts at _q_ 1, passes _p_ 3 and _q_ 2, and finally reaches _p_ 4. The cost of this path is _cf_ ( _q_ 1 _, p_ 3) + _cf_ ( _p_ 3 _, q_ 2) + _cf_ ( _q_ 2 _, p_ 4) = 0 _._ 1 + ( _−_ 0 _._ 6) + 0 _._ 9 = 0 _._ 4. SSP selects the feasible path with the _lowest cost_ and _augments_ the maximum possible flow along the path. The augmented flow is determined by the minimum of the following quantities: (i) the remaining flow capacity at the source node, (ii) the remaining flow capacity at the destination, (iii) the minimum remaining capacity of all edges on the path. For example, Figure 2(b) shows the result of augmenting the path shown by the three dashed lines in Figure 2(c). The augmentation adds 1 flow unit to all physical edges on the path (i.e., _e_ ( _q_ 1 _, p_ 3) and _e_ ( _q_ 2 _, p_ 4)), subtracts 1 flow unit from the edges, for which the reverse edge is on the path (i.e., _e_ ( _q_ 2 _, p_ 3)), and updates the capacities of path edges, _q_ 1, and _p_ 4. 

Computing the EMD, using SSP requires _O_ ( _F |E|log|V |_ ) time, where _F_ is the total number of flows we need to augment and _O_ ( _|E|log|V |_ ) is the cost of a shortest path search on a bipartite graph with _|V |_ vertices and _|E|_ edges. After each path augmentation, the _changes in the graph_ render the subsequent shortest path search _independent_ from the previous one, therefore, a large number of shortest path computations should be applied. As we shall see in Section 3, we can greatly reduce the cost of SSP by a method which builds and searches the flow graph incrementally. 

## **2.2** 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0003-11.png'>
The image contains a diagram illustrating a process flow divided into two phases: "filter phase" and "refinement phase." The flow is depicted along a horizontal axis labeled with "quick-and-dirty" on the left and "slow-and-accurate" on the right.

### Diagram Flow:
1. **Normal distribution index**: This is represented by a triangular shape pointing downward towards "Full projections."
2. **Full projections**: This box is connected to the "Dimensionality reduction" and "Independent minimization" boxes within the filter phase.
3. **Filter phase**: Contains two components:
   - **Dimensionality reduction**
   - **Independent minimization**
4. **Refinement phase**: Contains one component:
   - **Black-box EMD calculation**

The diagram indicates a progression from the normal distribution index through full projections and the filter phase (dimensionality reduction and independent minimization) to the refinement phase (black-box EMD calculation). The flow moves from left to right, transitioning from quick-and-dirty methods to slow-and-accurate methods.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
filter phase refinement phase<br>Normal distribution index<br>Dimensionality<br>reduction<br>Black-box EMD<br>calculation<br>Independent<br>Full projections minimization<br>quick-and-dirty  slow-and-accurate<br>**----- End of picture text -----**<br>


**Figure 4: Filter-and-refinement framework** 

Given a collection _D_ of histograms and a _query_ histogram **q** , a _k_ -nearest neighbor ( _k_ -NN) query, finds a subset _S_ of _D_ containing _k_ histograms, such that _∀_ **p** _∈S, ∀_ **p** _[′] ∈D \ S, emd_ ( **q** _,_ **p** ) _≤ emd_ ( **q** _,_ **p** _[′]_ ). The _k_ -NN query is the most popular similarity search type, as the number of results is controlled by _k_ and there is no requirement for setting a similarity threshold prior to search. In previous studies [5,7,25,30], _k_ -NN queries are evaluated based on a filter-and-refinement framework. The EMD _emd_ ( **q** _,_ **p** ) between the query histogram **q** and every histogram **p** _∈D_ is estimated with the help of lower bound filtering techniques, such as the _normal distribution index_ [25], the _full projection lower bound_ [7], the _reduced dimension lower bound_ [30], and _independent minimization_ [5]. In general, these filters are applied in an order starting from _quick-and-dirty_ ones to _slow-and-accurate_ ones, as shown in Figure 4. For histograms **p** that cannot be pruned by the filters, the actual _emd_ ( **q** _,_ **p** ) is calculated by a black-box computation module, such as SSP or transportation simplex [12]. 

315 

|**Algorithm 1**FILTER-AND-REFINEMENT FOR|**Algorithm 1**FILTER-AND-REFINEMENT FOR|_k_-NN|
|---|---|---|
||_H_: heap,_θ_: pruning threshold||
||**Algorithm**_k_-NN(Query**q**, Index_I_, Filters∆)||
|1:|_θ_ :=_∞_;_H_ :=_∅_||
|2:|**while**_I.getnext_(**q**_, θ, ⟨_**p**_, lb_**p**_⟩_)**do**||
|3:|**for**_δi ∈_∆**do**|_▷_Filter phase|
|4:|_lb_**p** := max_{lb_**p**_, δi_(**q**_,_**p**)_}_||
|5:|**if**_lb_**p** _≥θ_**then**break loop||
|6:|**if**_lb_**p** _< θ_**then**|_▷_Refnement phase|
|7:|**if**_emd_(**q**_,_**p**)_< θ_**then**||
|8:|update_H_ to include_⟨_**p**_, emd_(**q**_,_**p**)_⟩_||
|9:|_θ_ :=_k_-th EMD value in_H_||
|10:|**return**_H_||



Algorithm 1 is a pseudocode of the filter-and-refinement framework used in previous work. Since histograms correspond to objects (e.g., images), we will use the terms objects and histograms interchangeably. First, the framework accesses objects from an index _I_ , such as the _normal distribution index_ [25] or the _TBI index_ [32]. These indexes provide a _getnext_ function which returns at each call an unseen object **p** having lower bound _lb_ **p** of _emd_ ( **q** _,_ **p** ) smaller than a given threshold _θ_ (line 2). In _k_ -NN search, _θ_ is the _k_ -th largest EMD computed so far (i.e., the distance of the current _k_ -th NN of **q** in _D_ ). At each iteration (lines 2–9), the framework accesses a histogram **p** _∈D_ using the _getnext_ function and attempts to tighten its lower bound _lb_ **p** by applying a set ∆ of progressively more expensive and accurate lower bound estimation techniques (see Figure 4). If any of the computed lower bounds is not smaller than the pruning threshold _θ_ (line 5), then **p** is _filtered_ , i.e., the exact _emd_ ( **q** _,_ **p** ) needs not to be computed. Otherwise, _emd_ ( **q** _,_ **p** ) is essentially computed by a black-box algorithm (line 7). During search, Algorithm 1 maintains a heap _H_ with the _k_ histograms having the lowest EMD so far and the pruning threshold _θ_ (lines 8–9). The _k_ -NN candidates are confirmed as the result, when no more objects are returned by the _getnext_ function (line 2), i.e., all unseen objects do not satisfy the distance threshold _θ_ . 

## **3. SCALING UP SSP** 

Computing EMD by SSP requires having the complete bipartite graph between **q** and **p** , which is quadratic to the number of histogram bins. In our previous work, we proposed an optimized version of SSP, _simplified graph incremental algorithm_ (SIA) [29], to scale up the computation of _spatial matching_ problems. We now show how SIA can be adopted to scale up the computation of EMD, for histograms with a large number of bins. Different from SSP, SIA incrementally constructs a _partial_ flow graph _G[′]_ by inserting edges from the complete bipartite graph _G_ to _G[′]_ . The incremental graph construction significantly reduces the search cost since the size of the partial graph _G[′]_ is typically much smaller than the complete graph _G_ . We use the running example (cf. Figure 2) to demonstrate the superiority of SIA in Figure 5. Recall that the min-cost feasible path starting at _q_ 1 (cf. Figure 2(c)) is _q_ 1 _→ p_ 3 _→ q_ 2 _→ p_ 4 in the complete graph _G_ . Suppose a partial graph _G[′]_ is constructed based on the seen values in the partial cost matrix (Figure 5(b)), the same min-cost feasible path can be found in _G[′]_ as well. Thereby, augmenting this path in _G[′]_ is equivalent to the augmentation in _G_ which returns the same result in Figure 2(b). 

The question now turns to _how we can guarantee that the mincost feasible paths in G and G[′] are equivalent_ . This is done by a distance bound checking where the bound Π is derived from the edges not yet inserted into _G[′]_ . As an intuition, if the edges in _G[′]_ are inserted incrementally in ascending order to their costs at every vertex, it is possible that the min-cost path in _G[′]_ is cheaper than all 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0004-05.png'>
The image contains two parts: a partial graph \( G' \) and a cost matrix of \( G' \).

### (a) Partial graph, \( G' \)

This part shows a directed graph with nodes labeled as \( q_1, q_2, q_3, q_4 \) on the left side and \( p_1, p_2, p_3, p_4 \) on the right side. The edges between these nodes have weights associated with them:

- From \( q_1 \):
  - An edge to \( p_1 \) with weight \( 2/2 \).
  - An edge to \( p_2 \) with weight \( 0/3 \).
  - An edge to \( p_3 \) with weight \( 0/2 \).

- From \( q_2 \):
  - An edge to \( p_2 \) with weight \( 1/1 \).

- From \( q_3 \):
  - An edge to \( p_2 \) with weight \( 1/3 \).
  - An edge to \( p_3 \) with weight \( 2/4 \).

- From \( q_4 \):
  - An edge to \( p_3 \) with weight \( 2/2 \).
  - An edge to \( p_4 \) with weight \( 1/1 \).

Each node \( q_i \) has a label "0" next to it, and each node \( p_i \) has a label "0" except for \( p_4 \), which has a label "1".

### (b) The cost matrix of \( G' \)

This part shows a table representing the cost matrix of the graph \( G' \):

|       | \( p_1 \) | \( p_2 \) | \( p_3 \) | \( p_4 \) |
|-------|-----------|-----------|-----------|-----------|
| \( q_1 \) | 0         | -         | 0.1       | -         |
| \( q_2 \) | 0.9       | 0         | 0.6       | 0.9       |
| \( q_3 \) | -         | -         | 0         | -         |
| \( q_4 \) | -         | -         | -         | 0         |

The table entries represent the costs from nodes \( q_i \) to nodes \( p_j \). A dash (-) indicates no direct connection.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
q p<br>1 q1 2/2 p1 0<br>0/3 0/2<br>0 q2 1/1 p2 0 p 1 p 2 p 3 p 4<br>1/3 2/4 q 1 0 - 0.1 -<br>0 q3 2/2 p3 0 q 2 0.9 0 0.6 0.9<br>q 3 - - 0 -<br>0 q4 1/1 p4 1 q 4 - - - 0<br>(a) Partial graph,  G [′] (b) The cost matrix of  G [′]<br>**----- End of picture text -----**<br>


**Figure 5: SIA on a partial flow graph** 

feasible paths which include edges not in _G[′]_ . In this case, the path is augmented; otherwise SIA expands _G[′]_ by inserting more edges until the best feasible path in _G[′]_ has lower cost than the threshold Π[4] ; the expansion of _G[′]_ can only reduce the cost of the feasible flow and increase Π, as edges are inserted to _G[′]_ in increasing order of their costs. 

**Algorithm 2** SIA BASED EMD CALCULATION 

|**Alg**|**orithm 2**SIA BASEDEMD CALCULATION|
|---|---|
||Π: distance bound,_G′_: running subgraph|
||**Algorithm**_emdSIA_(Histograms**q**,**p**)|
|1:|Π := 0;_G′_ :=_∅_|
|2:|**while**_∃_feasible_qi_ **do**|
|3:|_sp_:=Dijkstra(_qi, G′_)|
|4:|**while**_sp.cost >_Πor_sp_doesn’t reach any feasible_pj_ **do**|
|5:|insert min-cost edge_e_(_ql, pm_)_∈G −G′_ into_G′_|
|6:|update distance boundΠ|
|7:|_sp_:=Dijkstra(_qi, G′_)|
|8:|augment_sp_|
|9:|**return**total augmenting cost|



Algorithm 2 is a pseudocode of SIA for EMD calculations. At each iteration, SIA searches the min-cost feasible path _sp_ using Dijkstra’s shortest path algorithm [1] in _G[′]_ from any feasible vertex (line 3), i.e., a vertex of **q** with remaining capacity.[5] If the cost of _sp_ does not exceed the distance bound Π (line 4), then it must be a valid min-cost feasible path in the entire graph _G_ . We augment the flow of _sp_ if _sp_ is valid (line 8). Otherwise, _G[′]_ is essentially expanded by adding more edges from _G_ (line 5) and the distance bound Π is updated accordingly (line 6). 

We demonstrate the functionality of SIA by the example of Figure 6. Suppose that _G[′]_ contains only 6 edges and there are 9 flow capacities sent already. According to the flow capacities, _q_ 1 is the only feasible node in **q** but there is no feasible path currently from _q_ 1 to any node of **p** (see Figure 6(a)). Subsequently, we insert a new edge, _e_ ( _q_ 1 _, p_ 3), into _G[′]_ and now there is a shortest path, _sp_ = _⟨e_ ( _q_ 1 _, p_ 3) _, e_ ( _p_ 3 _, q_ 2) _, e_ ( _q_ 2 _, p_ 4) _⟩_ . The cost of _sp_ is 0.4, which is smaller than the distance bound Π, thus we return _sp_ as the result of the current search and augment 1 unit of flow from _q_ 1 and _q_ 2 to _p_ 3 and _p_ 4, while 1 unit of flow from _q_ 2 to _p_ 3 is canceled. 

> 4For clarity, Π = _cmax_ ( _E − E′_ ) _− τmax_ , where _cmax_ ( _·_ ) returns the maximum cost in a set of edges, _E[′]_ denotes the edges in _G[′]_ , and _τmax_ indicates the largest potential value of the vertices. As a note, Π can be further tightened if considering only a subset of _E[′]_ where the edges are from the vertices being _visited_ by the current Dijkstra search. The correctness proof and optimization details are given in [29]. 

> 5Since _G_ (and _G′_ ) may contain edges of negative costs (i.e., the reverse of edges that currently carries flow), Dijkstra’s algorithm cannot be directly applied. To make its application possible, we need to iteratively maintain a _potential_ value at every vertex, which transforms the costs of the feasible edges to non-negative values. The details (see [29]) are omitted for the sake of readability. 

316 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0005-00.png'>
The image contains three diagrams labeled (a), (b), and (c), each depicting a state transition system with states labeled as \( q_1, q_2, q_3, q_4 \) and \( p_1, p_2, p_3, p_4 \). The transitions between states are represented by arrows with associated probabilities and values.

### Diagram (a): \( G' \) at loop \( i \)
- States: \( q_1, q_2, q_3, q_4 \) and \( p_1, p_2, p_3, p_4 \).
- Transitions:
  - \( q_1 \) to \( p_1 \) with \( 2/2 \).
  - \( q_2 \) to \( p_2 \) with \( 1/1 \).
  - \( q_3 \) to \( p_3 \) with \( 2/2 \).
  - \( q_4 \) to \( p_4 \) with \( 1/1 \).
  - \( q_2 \) to \( q_3 \) with \( 1/3 \).
  - \( q_3 \) to \( q_2 \) with \( 1/3 \).

### Diagram (b): \( G' \) at loop \( i + 1 \)
- States: \( q_1, q_2, q_3, q_4 \) and \( p_1, p_2, p_3, p_4 \).
- Transitions:
  - \( q_1 \) to \( p_1 \) with \( 2/2 \).
  - \( q_2 \) to \( p_2 \) with \( 0/3 \).
  - \( q_3 \) to \( p_3 \) with \( 2/4 \).
  - \( q_4 \) to \( p_4 \) with \( 1/1 \).
  - \( q_2 \) to \( q_3 \) with \( 1/3 \).
  - \( q_3 \) to \( q_2 \) with \( 1/3 \).

### Diagram (c): \( G' \) at loop \( i + 2 \)
- States: \( q_1, q_2, q_3, q_4 \) and \( p_1, p_2, p_3, p_4 \).
- Transitions:
  - \( q_1 \) to \( p_1 \) with \( 1/3 \).
  - \( q_2 \) to \( p_2 \) with \( 1/4 \).
  - \( q_3 \) to \( p_3 \) with \( 2/4 \).
  - \( q_4 \) to \( p_4 \) with \( 1/1 \).
  - \( q_2 \) to \( q_3 \) with \( 2/3 \).
  - \( q_3 \) to \( q_2 \) with \( 1/3 \).

Each diagram shows the evolution of the state transition system over successive loops, with changes in transition probabilities and values.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
q p q p q p<br>1 q1 2/2 p1 0 1 q1 2/2 p1 0 0 q1 2/2 p1 0<br>0/3 1/3<br>0 q2 1/1 p2 0 0 q2 1/1 p2 0 0 q2 1/1 p2 0<br>1/3 2/4 1/3 2/4 2/3 1/4<br>0 q3 2/2 p3 0 0 q3 2/2 p3 0 0 q3 2/2 p3 0<br>0 q4 1/1 p4 1 0 q4 1/1 p4 1 0 q4 1/1 p4 0<br>(a) G [′] at loop  i (b) G [′] at loop  i  + 1 (c) G [′] at loop  i  + 2<br>**----- End of picture text -----**<br>


**Figure 6: A running example of SIA-EMD** 

In this work, we use SIA as a module for computing the EMD between two histograms **p** and **q** in the refinement step of similarity search, due to its efficiency and scalability to the number of histogram bins. Still, SIA only optimizes the performance of an individual EMD calculation, whereas our ultimate objective is to minimize the overall cost of a similarity query, which may involve a large number of EMD calculations. The next section shows how we can optimize the overall cost of queries by exploiting information during the course of a SIA calculation. 

## **4. BOOSTING THE REFINEMENT PHASE** 

In this section, we propose two novel techniques, _progressive bounding_ (PB) and _dynamic refinement ordering_ (DRO), which boost the performance of the refinement phase during EMD-based similarity search. PB is inspired by the running time pattern of a single EMD calculation and DRO is inspired by the execution order in the filter-and-refinement framework. These two techniques make the EMD calculations at the refinement phase being handled in multiple stages and progressively instead of as one-off processes (i.e., by black-box modules). 

## **4.1 Analysis of EMD Calculation** 

According to previous experimental studies (e.g., [25,32]), more than 95% of the histograms on average can be filtered by the lower bound estimations; however, such high filter effectiveness is not guaranteed. To make things worse, if we process EMD-based similarity queries on large datasets (e.g., 1M objects) having highgranularity histograms (e.g., several hundreds of bins), the refinement phase even at a very high filtering ratio (e.g., 99%) easily becomes the bottleneck, due to the high cost of exact EMD calculations. Although there has been ample work on improving the performance and effectiveness of the filter phase in EMD-based similarity search, to the best of our knowledge, there has been no work focusing on optimizing the _refinement phase_ , for which offthe-shelf EMD computation techniques (such as transportation simplex or SSP) are simply applied as black-box modules. 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0005-07.png'>
The image contains two graphs:

### (a) SIA's cumulative runtime

This graph plots **Time (s)** on the y-axis against **Iterations** on the x-axis. The x-axis ranges from 0 to 3000 iterations, while the y-axis ranges from 0.00 to 0.6 seconds. There is a single line marked with 'x' symbols representing the cumulative runtime. The time increases gradually up to around 2500 iterations and then rises sharply towards the end.

---

### (b) Current cost

This graph plots **Cost** on the y-axis against **Iterations** on the x-axis. The x-axis ranges from 0 to 3000 iterations, while the y-axis ranges from 0.0 to 2.0. Four lines represent different metrics:
- **Current cost**: Marked with circles.
- **End**: Marked with squares.
- **Best bound from filter phase**: Marked with triangles.
- **Pruning threshold**: Marked with 'x' symbols.

All four lines show an increasing trend as the number of iterations increases. The "Current cost" line starts near zero and rises steadily. The "End" line follows closely behind. The "Best bound from filter phase" line also increases but stays slightly below the "Current cost." The "Pruning threshold" line remains relatively flat compared to the others.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
0.6 2.0 Current cost<br>emd [−]<br>Best bound from filter phase<br>1.5 Pruning threshold<br>0.4<br>1.0<br>0.2<br>0.5<br>0.0 0<br>0 500 1000 1500 2000 2500 3000 0 500 1000 1500 2000 2500 3000<br>Iterations Iterations<br>(a) SIA’s cumulative runtime (b) Current cost<br>Cost<br>Time (s)<br>**----- End of picture text -----**<br>


**Figure 7: SIA performance on different iterations** 

As discussed in Section 3, we adopt SIA for exact EMD calculations in the refinement phase. Although SIA offers great performance improvements over typical EMD solutions (e.g., SSP [1] and transportation simplex [12]), the running time during its execution increases quickly as the algorithm progresses. Figure 7(a) shows the cumulative runtime over SIA iterations during a typical EMD calculation for two histograms with 1024 bins each. This example shows that over 90% of SIA’s execution time is used in the last 20% of its iterations. The reason behind this is that as SIA progresses, the partial graph _G[′]_ and the number of feasible edges grow and shortest path searches become much more expensive. This analysis shows that there is room for greatly improving the refinement phase of EMD-based similarity search, if SIA can be terminated before reaching its late iterations. 

## **4.2 Progressive Bounding** 

In order to terminate SIA as early as possible for objects that do not make it to the query result set, we propose a technique which _progressively_ maintains a _running lower bound emd[−]_ and tightens _emd[−]_ throughout the entire EMD calculation process. SIA, for a specific refinement, can terminate early if the running lower bound becomes not smaller than the current pruning threshold _θ_ (i.e., the _k_ -th lowest EMD found so far). 

First, we use a property of SSP (and SIA); at each iteration, the minimum-cost feasible path is nonnegative when the cost matrix **C** does not include any negative values [1]. In other words, the accumulated cost by augmenting flows at each iteration is monotonically non-decreasing, and can be used as the running lower bound of EMD. For example, Figure 7(b) illustrates the accumulation of the EMD during SIA, for two 1024-bin histograms **q** and **p** . At each iteration, the _current cost_ represents the accumulation of the augmented costs up to that iteration; by comparing it with the current pruning threshold _θ_ (ignore the other series for the moment), we can observe that SIA may terminate as soon as the current cost becomes at least equal to _θ_ (i.e., at around 88.3% of the total iterations). This point corresponds to 23.4% of SIA’s total execution time (cf. Figure 7(a)). Note that the current cost remains 0 until the 1024th iteration because the shortest paths up to this iteration correspond to flows between the same bins of **q** and **p** (i.e., from _qi_ to _pi_ for some _i ∈_ [1 _, n_ ] _, n_ = 1024) with zero cost each. 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0005-13.png'>
The image contains a diagram illustrating a process involving cost computation and estimation. Here's a breakdown:

### Diagram Description:
1. **Boxes with Arrows:**
   - There are three boxes connected by arrows indicating flow or relationships.
   - The first box contains four smaller boxes labeled as follows:
     - Top left: `1 q_r` with an arrow labeled `2` pointing to `p_r 0`.
     - Top right: `1 q_s` with an arrow labeled `1` pointing to `p_s 0`.
     - Bottom left: `0 q_j` with an arrow labeled `2` pointing to `p_j 0`.
     - Bottom right: `1 q_h` with an arrow labeled `2` pointing to `p_h 3`.
   - The second box is labeled "current cost" and has an arrow pointing from the first box to it. This arrow is labeled "computed by."
   - The third box is labeled "estimated cost" and has an arrow pointing from the first box to it. This arrow is labeled "estimated by."

2. **Operations and Labels:**
   - The "current cost" box has an arrow pointing to a block labeled "SIA / SSP."
   - The "estimated cost" box has an arrow pointing to a block labeled "lower bound estimation."
   - Both the "SIA / SSP" and "lower bound estimation" blocks have arrows pointing to a final block labeled `emd*`.

3. **Mathematical Symbols:**
   - A plus sign (`+`) is shown between the "SIA / SSP" and "lower bound estimation" blocks, indicating some form of combination or addition.

This diagram appears to represent a computational process where costs are computed and estimated, then combined to produce a final value `emd*`.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
1 qr 2/2 pr 0<br>current cost SIA / SSP<br>1 qs 1/1 ps 0<br>2/4 computed by emd [-]<br>0 qj 2/2 pj 0 estimated  lower bound<br>cost estimtaion<br>1 qh ph 3<br>**----- End of picture text -----**<br>


**Figure 8: Running lower bound,** _emd[−]_ 

Although the _current cost_ could be intuitively used as a lower bound for the final (actual) EMD, it is not sufficiently tight since it does not take the remaining feasible flow into consideration. Thereby, we propose a _running lower bound_ , _emd[−]_ , which not only considers the so-far accumulated flow cost, but also provides an estimation to the cost of flows yet to be augmented. As Figure 8 illustrates, _emd[−]_ consists of the _current cost_ (partial EMD already computed) plus a lower bound for the cost of the remaining flow. The effectiveness of _emd[−]_ is shown in the running example of Figure 7(b), where _emd[−]_ grows much faster compared to the 

317 

_current cost_ and leads to an early termination of SIA for EMD calculations. In this example, the running lower bound _emd[−]_ reaches the pruning threshold _θ_ after augmenting 61% iterations which take only 2.84% of the total execution time. This result demonstrates the effectiveness of _emd[−]_ in boosting EMD-based similarity search. 

We now formally define _emd[−]_ . First, Lemma 1 shows that the costs of the minimum-cost feasible paths being augmented from a vertex are monotonically non-decreasing, which forms a basis for 

LEMMA 1 (COST MONOTONICITY OF FEASIBLE PATHS). _Given a flow graph for which there is a sequence of mi minimum-cost feasible paths spqi,_ 1 _, . . . , spqi,mi from a node qi ∈_ **q** _already been augmented in this order, the cost of these paths from qi is monotonically non-decreasing, i.e., cf_ ( _spqi,j_ ) _≤ cf_ ( _spqi,k_ ) _, ∀_ 1 _≤ j < k ≤ mi._ 

PROOF. To prove the statement, it suffices to show that the cost of the shortest path from any _qi ∈_ **q** to any _pj ∈_ **p** is monotonically non-decreasing throughout the entire flow augmentation process; i.e., _c[t] f[−]_[1] ( _qi_ ⇝ _pj_ ) _≤ c[t] f_[(] _[q][i]_[⇝] _[p][j]_[)][,][where] _[c][t] f_[is][the][cost][of][the] shortest path from _qi_ to _pj_ after _t_ augmentations. If this holds, then the cost of the minimum-cost feasible paths from _qi_ must be monotonically non-decreasing, because at each iteration, SIA picks for _qi_ the path with the minimum cost, and there is always a feasible path between any pair of nodes with remaining capacity. We prove this by contradiction. Assume that the monotonicity of the shortest path cost from _qi_ to a vertex _pj_ does not hold, i.e., _c[t] f[−]_[1] ( _qi_ ⇝ _pj_ ) _> c[t] f_[(] _[q][i]_[⇝] _[p][j]_[)][,][and][assume][that][no][path][vio-] lates the monotonicity property until the _t_ -th iteration. In addition, among all paths that violate the monotonicity property at the _t_ -th iteration, _c[t] f_[(] _[q][i]_[⇝] _[p][j]_[)][has][the][minimum][cost.][Suppose][that] _[q][k]_[is] the preceding vertex of _pj_ in the shortest path, we have 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-04.png'>
The image contains a mathematical expression:

\[ c_f^t(q_i \sim p_j) = c_f^t(q_i \sim q_k) + c_f^t(q_k, p_j) \geq c_f^t(q_i \sim q_k). \]

There are no tables, charts, graphs, diagrams, flowcharts, or other visual elements present in the image.
</IMAGE_CONTEXT>




In addition, based on our assumption, no vertex violates the monotonicity property before the _t_ -th augmentation. Thereby, 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-06.png'>
The image contains a mathematical inequality:

\[ c_{t}^{t-1}(q_k \leadsto q_k) \leq c_{t}^{t}(q_k \leadsto q_k) \]

This expression compares two terms involving \( c_t \), with subscripts and superscripts indicating different time steps \( t \) and \( t-1 \). The terms involve a transition from state \( q_k \) to itself.
</IMAGE_CONTEXT>




By combining the equations, we get 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-08.png'>
```markdown
|                             |                     |                             |                              |                             |                               |
|-----------------------------|---------------------|-----------------------------|------------------------------|-----------------------------|-------------------------------|
| $c_{f}^{t-1}(q_i \leadsto p_j)$|    >    | $c_f^t(q_i \leadsto p_j)$ |    ≥    | $c_f^t(q_i \leadsto q_k)$   | ≥ $c_{f}^{t-1}(q_i \leadsto q_k)$ |
```
</IMAGE_CONTEXT>







<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-09.png'>
The image contains a mathematical inequality involving cost functions \( c_f^t \) with variables \( q_i \), \( p_j \), \( q_k \), and \( p_j \). The inequality is as follows:

\[ c_f^{t-1}(q_i \leadsto p_j) \leq c_f^{t-1}(q_i \leadsto q_k) + c_f^{t-1}(q_k, p_j) \]

\[ \leq c_f^t(q_i \leadsto q_k) + c_f^t(q_k, p_j) = c_f^t(q_i \leadsto p_j); \]
</IMAGE_CONTEXT>







<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-10.png'>
otherwise (e(pj), qk) is feasible in G^(t-1):
</IMAGE_CONTEXT>







<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-11.png'>
The image contains a mathematical inequality involving cost functions \( c_f^t \). The inequality compares the cost of transitioning from state \( q_i \) to state \( q_k \) with the sum of costs for intermediate transitions. Here is the transcription:

\[
c_f^{t-1}(q_i \leadsto q_k) \geq c_f^{t-1}(q_i \leadsto p_j) + c_f^{t-1}(q_k, p_j)
\]

\[
> c_f^t(q_i \leadsto p_j) + c_f^t(q_k, p_j) \geq c_f^t(q_i \leadsto q_k).
\]
</IMAGE_CONTEXT>




Both cases contradict our assumptions. 

DEFINITION 3 (RUNNING LOWER BOUND, _emd[−]_ ). _Consider a flow graph, such that for each node qi ∈_ **q** _, there is a set of mi augmented paths spqi,_ 1 _, . . . , spqi,mi . The running lower bound emd[−] is defined as_ 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0006-14.png'>
The image contains a mathematical equation:

\[ emd^- = \sum_{q_i \in \mathbf{q}} \sum_{j=1}^{m_i} c_f(sp_{q_i,j}) \cdot f(sp_{q_i,j}) + \quad (\text{current cost}) \]

\[ \sum_{q_i \in \mathbf{q}} c_f(sp_{q_i,m_i}) \cdot (cap_{q_i} - f_{q_i}), \quad (\text{estimated cost}) \]
</IMAGE_CONTEXT>




_where capv indicates the total flow capacity of node v, and fv indicates the flow units already augmented from v so far._ 

LEMMA 2 (CORRECTNESS OF _emd[−]_ ). _The running lower bound emd[−] is monotonically non-decreasing and always not greater than emd_ ( **q** _,_ **p** ) _throughout the EMD calculation._ PROOF. Trivial, due to the monotonicity of the shortest path costs from any vertex _qi_ (Lemma 1) and due to the fact that all remaining flow _capqi − fqi_ at _qi_ should be augmented in paths originating at _qi_ . 

**Table 2: Four augmented paths and their costs** 

|iteration|feasiblepath|_cf_(_spi_)|_f_(_spi_)|current cost|
|---|---|---|---|---|
|1|_sp_1 = _⟨e_(_q_1_, p_1)_⟩_|0.0|2|0.0|
|2|_sp_2 = _⟨e_(_q_3_, p_3)_⟩_|0.0|2|0.0|
|3|_sp_3 = _⟨e_(_q_2_, p_2)_⟩_|0.0|1|0.0|
|4|_sp_4 = _⟨e_(_q_2_, p_3)_⟩_|0.6|2|1.2|



Using Definition 3, we can compute _emd[−]_ by adding to _current cost_ an estimated lower bound for all remaining feasible paths originating at each vertex _qi_ , based on the node’s remaining capacity _−_ (i.e., _capqi fqi_ ) and the cost of the last augmented feasible path from _qi_ . Lemma 2 proves the correctness of the bound. The example of Figure 8 illustrates the computation of _emd[−]_ . There are 4 paths already augmented; their costs and iteration order are shown in Table 2. The current cost is 1.2 (= _cf_ ( _sp_ 4) _f_ ( _sp_ 4) = 0 _._ 6 _·_ 2) and the estimated cost of the remaining flows (computed using the nodes of **q** in the dashed-line region) is 0.6 (= _cf_ ( _sp_ 4)( _capq_ 2 _− fq_ 2 ) = 0 _._ 6 _·_ (4 _−_ 3)). Thereby, _emd[−]_ is 1.8 which is much tighter compared to just using the _current cost_ as the lower bound. 

Note that the time of updating _emd[−]_ during SIA is negligible. Whenever a new feasible path _sp_ from a vertex _qi_ is augmented (i.e., at each iteration of SIA), we refine _emd[−]_ by: (i) adding the augmentation cost of _sp_ ( _cf_ ( _sp_ ) _· f_ ( _sp_ )) to the current cost component of _emd[−]_ ; (ii) subtracting the previous estimated cost for _qi_ in the estimated cost component; (iii) adding the new estimated cost of _qi_ . Each of these three increments takes constant time (in fact, (ii) is already cached), so the update of _emd[−]_ takes _O_ (1) time. 

Summing up, our _progressive bounding_ (PB) approach, during the EMD calculation for a candidate, progressively maintains and tightens the running lower bound _emd[−]_ and prunes the object as soon as the intermediate _emd[−]_ reaches the pruning threshold _θ_ . PB saves unnecessary computations at the latter (expensive) stages of SIA for candidate objects that do not make it to the _k_ -NN result (i.e., conducting only the necessary portion of the entire flow calculation), and thus reduces the cost of each individual refinement. 

## **4.3 Sensitivity to Refinement Order** 

So far, we have discussed how to terminate a single EMD calculation early by the _progressive bounding_ technique. Still, the performance of a _k_ -NN query does not depend only on individual EMD calculations but also on the amount and progresses of EMD calculations. According to Algorithm 1, the EMD for an object **p** is essentially refined if all estimated lower bounds _lb_ **p** (at the filter phase) are smaller than the pruning threshold _θ_ (line 6 of Algorithm 1), where _θ_ is the _k_ -th best-so-far EMD value. 

Figure 9 shows the EMD values of the accessed objects during a 4-NN query execution using Algorithm 1. For each candidate **p** , a bar shows the real EMD value _emd_ ( **q** _,_ **p** ), the best lower bound _lb_ **p** from the filter phase, and the pruning threshold _θ_ at the time of **p** ’s verification. Every refined candidate can potentially decrease the pruning threshold _θ_ if it replaces another object in the current _k_ -NN set _H_ . For instance, _θ_ is decreased after accessing and refining the 6-th object. Observe that the order by which the objects are accessed is not consistent with their real EMD values. On the other 

318 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0007-00.png'>
The image contains a bar chart with the following details:

### Chart Description:
- **Title:** Not explicitly provided but implied by labels.
- **X-axis Label:** Access order (ranging from 0 to 40).
- **Y-axis Label:** EMD (ranging from 0.0 to 2.0).

### Key Values:
- The chart compares three datasets across different access orders:
  - Best bound from filter phase (represented by white bars with black outlines).
  - Real EMD (represented by gray bars with black outlines).
  - Pruning threshold (represented by a dashed line with black dots).

### Observations:
- The "Best bound from filter phase" consistently remains below the "Real EMD."
- The "Pruning threshold" is depicted as a horizontal dashed line intersecting the bars at certain points.
- A specific point labeled \( p_5 \) is marked on the chart near the intersection of the pruning threshold and one of the bars.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
2.0<br>Best bound from filter phase Real EMD<br>1.5 Pruning threshold<br>p5<br>1.0<br>0.5<br>0.0<br>10 20 30 40<br>Access order<br>EMD<br>**----- End of picture text -----**<br>


**Figure 9: Access order of a** _k_ **-NN search** 

hand, the amount of EMD calculations would have been greatly reduced if we had considered the objects in a better order. For instance, if we had accessed the 6-th and 7-th objects before the 5-th object **p** 5, then **p** 5 would have been filtered since its best lower bound would have been larger than _θ_ in this case. Note that a better access order not only filters more objects, but also decreases the pruning threshold _θ_ faster such that individual EMD calculations can be _terminated earlier_ owing to the _progressing bounding_ technique. Unfortunately, the access order of the state-of-the-art filterand-refinement framework is based on the _getnext_ function (provided by the _normal distribution index_ [25] or the _TBI index_ [32]), which just returns any unseen object **p** having lower bound smaller than a given threshold _θ_ . As shown in this example, there is room to improve the access order such that objects that are likely to have smaller EMD values have higher chances to be refined earlier. Motivated by this analysis, we propose a novel technique that defines and follows a dynamic access order of the candidates. 

## **4.4 Dynamic Refinement Ordering** 

The main idea behind our _dynamic refinement ordering_ (DRO) approach in refining candidates during EMD-based similarity search is to conduct the refinement for multiple candidates _concurrently_ . Thus, given a _priority layer PL_ set of _b_ candidates ( _PL ⊆D_ ), such that each **p** _∈ PL_ passes all filters based on the current threshold _θ_ , the objective of DRO is to refine all objects in _PL_ concurrently, by augmenting paths to the EMD of **p** _∈ PL_ , which is currently the most _promising_ object in _PL_ . Intuitively, an object is promising to augment flows on its corresponding EMD, if the augmentations can make the threshold _θ_ lower or prune objects from _PL_ . For instance, the running lower bound _emd[−]_ can be used to prioritize objects, since augmenting an object having the lowest _emd[−]_ may update the best _k_ objects found so far and decrease the threshold _θ_ early. The augmentations result in the increase (i.e., tightening) of _emd[−]_ **p** 6, which may cause another object **p** _′_ to take the place of **p** as the most promising one and be refined by DRO in the next step. Thus, DRO always refines the object **p** with the currently best promising value and checks whether **p** can be pruned after updating (i.e., increasing) _emd[−]_ **p**[. If this pruning happens,] **[ p]**[ is] replaced by another candidate object in _PL_ . DRO also keeps track of the _upper bound emd_[+] **p**[for each object] **[ p]** _[ ∈][PL]_[; if the currently] refined object’s upper bound becomes smaller than _θ_ , then the current top- _k_ result is updated to include **p** . The details on how to compute and update an upper bound of a partially computed EMD are given in Section 4.5. DRO continues until _PL_ becomes empty. 

Algorithm 3 is a pseudocode of the DRO strategy for EMDbased _k_ -NN search. DRO uses function _getnext_ ~~_f_~~ _ilter_ to get the next object from _D_ , which passes all filters with respect to the current threshold _θ_ . First, DRO calls this function _b_ times to form the initial _PL_ . _PL_ is stored as a priority queue, in which the top 

> 6For the ease of presentation, we denote _emd−_ ( **q** _,_ **p** ) by _emd−_ **p**[, as] the query histogram **q** is the same for all objects in _D_ . 

|**Algorithm 3**DYNAMICREFINEMENT|**Algorithm 3**DYNAMICREFINEMENT|ORDERING|ORDERING|ORDERING|
|---|---|---|---|---|
||_H_,_PL_: heap,_θ_: pruning threshold||||
||**Function**getnext<br>~~f~~lter(Query**q**, Index|_I_,|Filters|∆)|
|1:|**while**_I.getnext_(**q**_, θ, ⟨_**p**_, lb_**p**_⟩_)**do**||||
|2:|**for**_δi ∈_∆**do**|||_▷_Filter phase|
|3:|_lb_**p** := max_{lb_**p**_, δi_(**q**_,_**p**)_}_||||
|4:|**if**_lb_**p** _≥θ_**then**break loop||||
|5:|**if**_lb_**p** _< θ_**then**return_⟨_**p**_, lb_**p**_, ∞⟩_||||
||**Algorithm**DRO-_k_NN(Query**q**, Index|_I_, size_b_)|||
|6:|_θ_ :=_∞_;_H_ :=_∅_;_PL_:=_∅_||||
|7:|**while**_|PL| < b_**do**||||
|8:|_PL_:=_PL ∪_getnext<br>~~f~~lter(**q**,_I_,∆)||||
|9:|**while**_|PL| _=_∅_**do**||||
|10:|pop_⟨_**p**_, emd−_<br>**p** _, emd_+<br>**p** _⟩_from_PL_|||_▷_e.g., lowest_emd−_<br>**p**|
|11:|**while**_emd−_<br>**p** _< PL.top_()_.emd−_**do**||||
|12:|augment next shortest path in_emd_(**q**_,_**p**)||||
|13:|**if**_emd−_<br>**p** _≥θ ∨emd−_<br>**p** =_emd_+<br>**p **||**then**||
|14:|_PL_:=_PL ∪_getnext<br>flter(**q**,_I_,∆)||||
|15:|break loop||||
|16:|**if**_emd_+<br>**p** _< θ_**then**||||
|17:|update_H_ to include the new_⟨_**p**_, emd_+<br>**p** _⟩_||||
|18:|_θ_ :=_k_-th EMD value in_H_||||
|19:|**for all p**_∈PL_such that_emd−_<br>**p** _≥θ_**do**||||
|20:|remove**p**from_PL_||||
|21:|_PL_:=_PL ∪_getnext<br>~~f~~lter(**q**,_I_,|||∆)|
|22:|**if**loop not broken**then**||||
|23:|_PL_:=_PL ∪_**p**|||_▷_add**p**back to_PL_|
|24:|**return**_H_||||



element is the object with the smallest _emd[−]_ . At each iteration, DRO de-heaps the top object **p** in _PL_ and progressively refines the current _emd_ ( **q** _,_ **p** ) by iteratively augmenting shortest paths (i.e., using SIA) while _emd[−]_ **p**[is still smaller than] _[ PL.top]_[()] _[.emd][−]_[(i.e,] the smallest _emd[−]_ in _PL_ ). A path augmentation increases _emd[−]_ **p** and decreases _emd_[+] **p**[.][If] _[emd][−]_ **p** _[≥][θ]_[,][then][the][current][object] **[p]** is pruned because in the best case it cannot become better than the current _k_ nearest neighbors (see Section 4.2); DRO calls function _getnext_ ~~_f_~~ _ilter_ to add another candidate in _PL_ in place of **p** (line 14). If _emd_[+] **p** _[<][θ]_[,] **[p]**[ is updated in] _[ H]_[and the threshold] _[ θ]_[is] updated accordingly (line 18). After _θ_ is updated, we remove from _PL_ objects whose lower bounds are already greater than or equal to _θ_ (line 19). The removal is facilitated by an additional heap structure that indexes objects in descending order of their lower bounds. If, after some augmentations, _emd[−]_ **p**[becomes no smaller] than _PL.top_ () _.emd[−]_ (line 11) and **p** has not been pruned, it is put back to _PL_ (line 23) and the top object of _PL_ takes its place in the inner path augmentation loop. Note that objects that may not be further refined (i.e., condition _emd[−]_ **p**[=] _[emd]_[+] **p**[at][line][13)][are] either pruned (if _emd_ **p** _≥ θ_ ) or added to _H_ (if _emd_ **p** _< θ_ ). 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0007-09.png'>
The image contains a bar chart with the following features:

### Chart Description:
- **Title:** The chart has no explicit title but includes labels for "Pruning threshold, θ" and "PL".
- **Bars:** There are seven bars labeled as \( p_1 \), \( p_2 \), \( p_3 \), \( p_4 \), \( p_5 \), \( p_6 \), and \( p_7 \).
- **Threshold Line:** A horizontal dashed line represents the pruning threshold, denoted by \( \theta \). This line intersects some of the bars.
- **Highlighted Region:** Bars \( p_4 \) and \( p_5 \) are shaded gray, indicating they exceed the pruning threshold \( \theta \).

### Key Values:
- The heights of the bars vary, with \( p_4 \) being the tallest and exceeding the threshold significantly. Bars \( p_5 \) also exceeds the threshold slightly. Other bars (\( p_1 \), \( p_2 \), \( p_3 \), \( p_6 \), and \( p_7 \)) remain below the threshold.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
PL<br>Pruning<br>threshold,  θ p4 p6 p7<br>p1 p2 p5<br>p3<br>**----- End of picture text -----**<br>


**Figure 10: Prioritizing refinement order** 

Figure 10 illustrates a running instance of DRO. The current lower and upper bounds of each object are indicated by the borders of a bar. Suppose _k_ = 3 and there are 7 objects (= _b_ ) in _PL_ . 

319 

Note that the currently best object in _PL_ (in terms of _emd[−]_ ) is **p** 4, so DRO refines the current EMD of **p** 4 by augmenting flows. After the augmentation, the EMD bounds of **p** 4 are updated to the shaded bar. Note that _emd[−]_ **p** 5[now][becomes][the][lowest] _[emd][−]_[,][so] the refinement of **p** 4 is stalled; in the next iteration, **p** 5 is de-heaped from _PL_ and refined. After augmenting flows to the EMD of **p** 5, the EMD bounds of **p** 5 are updated as shown by the shaded bar. Observe that now _emd_[+] **p** 5 _[<][θ]_[; this causes (i)] **[ p]** 5[to be included in] the currently best _k_ objects _H_ and (ii) _θ_ to be updated to _emd_[+] **p** 2[.] 

DRO is expected to be more efficient than considering the candidates that pass the filters one by one and computing their exact EMD individually. Concurrent refinement by prioritizing candidates with the lowest _emd[−]_ performs the first (cheap) iterations of SIA for many candidates and helps in deriving upper bounds _emd_[+] for them and a good estimate of _θ_ early. Obtaining a tight _θ_ early can help (i) to prune more candidates using the filters (function _getnext_ ~~_f_~~ _ilter_ ) and (ii) to avoid the late and expensive path augmentations of SIA for many candidates in _PL_ that can be pruned. 

The choice of _b_ (i.e., the size of _PL_ ) affects the performance of DRO; if _b_ is very large, DRO performs multiple concurrent SIA executions which may have high memory requirements. If _b_ is too small, the pruning threshold _θ_ does not converge fast to its final value, and more objects enter the refinement phase. Clearly, there is a tradeoff between the performance gain and memory consumption. In our experiments, every SIA thread only constructs a small portion of the entire flow graph. Thereby, _b_ can be set to a relatively large number. For instance, when _b_ is set to 0.2% of the data cardinality, the peak memory consumption of DRO on the largest dataset of our experimental evaluation, WORLD, is just around 20 times of a complete flow graph in a single EMD computation. Moreover, we study a mechanism to avoid worst cases (e.g., every partial graph in _PL_ is full). When the size of _PL_ exceeds a limit, we stop inserting candidates into _PL_ and refine the current EMD by PB until it is pruned or becomes a _k_ -NN candidate. However, in all of our experimental testings, this mechanism is never triggered as the size of _PL_ is much smaller than our default memory limit (i.e., 512MB). 

## **4.5 Running Upper Bound** 

We now discuss the details of computing and maintaining a _running upper bound emd_[+] **p**[for an object] **[ p]**[ whose EMD has partially] been computed by SIA. The upper bounds are used by DRO (presented in Section 4.4) to derive a value for _θ_ after having partially computed the EMD of some candidate objects. According to the EMD definition, any flow matrix **F** satisfying all three conditions of Equation 2 must lead to an upper bound of the actual EMD. For the ease of discussion, we call a flow matrix **F** _possible_ if it satisfies all these three optimization constraints; the constraints are satisfied if and only if there is no more feasible path in the flow network. Thus, finding a possible flow matrix **F** is equivalent to finding a maximum flow in the network [1], disregarding edge costs. 

Based on the above discussion, we can define a running upper bound _emd_[+] following the same idea of deriving _emd[−]_ . Similar to the illustration in Figure 8, _emd_[+] consists of the _current cost_ plus an upper bound considering the nodes which still have remaining flow capacity (i.e., the vertices inside the dashed-line regions). For instance, a maximum flow of the vertices inside the dashed-line region is ( _q_ 1 _, p_ 4 _,_ 1), ( _q_ 2 _, p_ 4 _,_ 1), and ( _q_ 4 _, p_ 4 _,_ 1). The cost of this max flow is 0.7 + 0.9 + 0 = 1.6; thus, _emd_[+] is 1.2 ( _current cost_ ) + 1.6 = 2.8. Formally, we define the running upper bound as follows. 

DEFINITION 4 (RUNNING UPPER BOUND, _emd_[+] ). _Consider a flow graph, such that for each node pi ∈_ **p** _, there is a set of mi augmented paths spqi,_ 1 _, . . . , spqi,mi . The_ 

_running upper bound emd_[+] _is defined as_ 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0008-08.png'>
The image contains a mathematical equation with annotations for parts of the equation:

\[ emd^+ = \sum_{q_i \in \mathbf{q}} \sum_{j=1}^{m_i} c_f(sp_{q_i,j}) \cdot f(sp_{q_i,j}) + \quad \text{(current cost)} \]

\[ \max \text{flow}(\mathbf{q}, \mathbf{p}), \quad \text{(maximum flow)} \]
</IMAGE_CONTEXT>




_where maxflow_ ( **q** _,_ **p** ) _returns the cost of a maximum flow based on the remaining capacities of_ **q** _and_ **p** _._ 

To compute _emd_[+] , we can apply any maximum flow algorithm; however, existing maximum flow algorithms are too expensive [1], considering the fact that _emd_[+] should be maintained throughout the entire EMD calculation. Instead of using these methods, we propose an efficient greedy approach, which takes advantage of the EMD flow network topology; note that the EMD flow graph is a _complete_ bipartite graph between the bins of **q** and **p** . This means that a feasible vertex of **q** can always augment flow to any feasible vertex of **p** along one edge. Our GreedyUB algorithm (Algorithm 4), for each feasible vertex _qi_ of **q** , accesses the feasible vertices _pj_ of **p** in increasing order of _ci,j_ and augments the maximum possible flow along each edge _e_ ( _qi, pj_ ), until the remaining capacity from _qi_ has been used up. The accumulated cost of the greedily augmented flows is used as the maxflow component _maxflow_ ( **q** _,_ **p** ) of _emd_[+] ( **q** _,_ **p** ). 

**Algorithm 4** GREEDY UPPER BOUND 

|**Alg**|**orithm 4**GREEDYUPPERBOUND||
|---|---|---|
||**Algorithm**GreedyUB(Histograms**q**,**p**)||
|1:|_cost_:= 0||
|2:|**while**_∃_feasible_qi_ **do**||
|3:|**while**_capqi > fqi_ **do**|_▷qi_ has remaining capacity|
|4:|_pj_ :=feasible bin in**p**having minimum_ci,j_||
|5:|_flow_ := min_{capqi −fqi, cappj −fpj }_||
|6:|_fqi_ :=_fqi_ +_flow_||
|7:|_fpi_ :=_fpi_ +_flow_||
|8:|_cost_:=_cost_+_ci,j · flow_||



9: **return** _cost_ 

To facilitate GreedyUB, for each row _i_ of the cost matrix **C** , we define an order for the bins _j_ based on _ci,j_ (this order is static, i.e., independent of the data and queries, and it is defined once, together with the ground distance function or cost matrix). For example, for row _q_ 1 of the matrix shown in Table 1, the order is _{p_ 1 _, p_ 3 _, p_ 4 _, p_ 2 _}_ . Then, in Algorithm 4 line 4, this order is considered for identifying feasible bins _pj_ for the current vertex _qi_ . Thus, the complexity of the greedy algorithm is _O_ ( _|E|_ ), where _E_ indicates the edges in the graph, since there are at most _|E|_ feasible pairs in the EMD flow graph, i.e., much lower compared to the complexity of standard maximum flow algorithms (e.g., _O_ ( _|V ||E|_ )). 

Similar to _emd[−]_ , we can update _emd_[+] incrementally after each path augmentation during the refinement of an EMD. After every augmentation of SIA, according to the capacity feasibility, we cancel and re-augment (for those that become feasible after the cancelation) the corresponding flows in the maximum flow graph formed by the greedy algorithm. The number of canceled/re-augmented edges in the maximum flow instance is at most equal to the flow units _f_ just being augmented in the current EMD flow. Thereby, the maintenance cost of _emd_[+] after each augmentation is _O_ ( _f_ ). 

## **5. EXPERIMENTAL EVALUATION** 

In this section, we conduct extensive experiments to evaluate the performance of our proposed EMD-based similarity search framework and compare it with state-of-the-art solutions. All methods are implemented in C++ and evaluated on 3.40 GHz quad-core machines running Ubuntu 12.04, with 16 GBytes of main memory. 

320 

**Table 3: The statistics of six real datasets** 

|Name|# Objs|# Bins|Description|
|---|---|---|---|
|RETINA|3932|96<br>(12_×_8)|Feline retina images.<br>Default dataset in[25,30,32].|
|IRMA|10K|199|Medical images from IRMA7<br>project. Used in[25,30,32].|
|FLICKR|680K|100<br>(10_×_10)|Images crawled from Flickr8.<br>This dataset is used in[25].|
|PANORAMIO|500K|576<br>(24_×_24)|Images of European cities from<br>Panoramio9.|
|FRIENDS|320K|768<br>(24_×_32)|Images captured every 25 frames<br>from the TV series “Friends”.|
|WORLD|3M|1024<br>(32_×_32)|Images from ImageNet10 project.|



We use six real datasets in our evaluation; their default statistics are shown in Table 3. The RETINA, IRMA and FLICKR histogram sets are taken from [25]. The PANORAMIO, FRIENDS and WORLD histogram sets are generated by the same method with RETINA and FLICKR as suggested in [25]: each image is divided into tiles by a grid (e.g., 24 _×_ 24 square granularity); for each tile, the 12-feature MPEG-7 color layout descriptor (CLD) is extracted, and we pick only the first feature as the value of the histogram bin. Similar to [25,30,32], we use Euclidean distance as the ground distance (cost matrix) in all the experiments. Note that our techniques are not restricted to any specific ground distance. 

In the evaluation, we compare a set of EMD computation methods when used as a black-box module of the filter-and-refinement framework (see Section 2.2). In all cases, the filtering of candidates is done by applying the state-of-the-art filtering techniques as used in [25]. First, we use the normal distribution index [25] to implement the _I.getnext_ function. For each retrieved candidate by this function, we apply the following set of filters ∆ in this order: full projection [7], reduced dimension [30] (only for RETINA and IRMA, on which the filter has positive effects as in [25]), and independent minimization [5]. For the candidates that pass the filter phase, we compare the application of the following EMD computation methods: (i) capacity scaling (CAP), (ii) cost scaling (COS), (iii) transportation simplex (TRA), (iv) network simplex (NET), (v) SSP (Section 2.1), (vi) SIA (Section 3). In addition, we evaluate our progressive bounding (PB) and dynamic refinement ordering (DRO) techniques when applied in conjunction with SIA. At each experimental instance (e.g., for a given dataset and _k_ ), we run 100 _k_ -NN queries choosing **q** randomly from the corresponding dataset and average the query cost. The 100 queries for RETINA, IRMA and FLICKR dataset are the same queries used in [25,30,32]. The default value of _k_ is 32 and the default _b_ (i.e., maximum size of _PL_ in DRO) is set to 0.2% of the corresponding dataset cardinality. 

## **5.1 Performance Improvement** 

First, we compare the performance of different black-box EMD computation methods in the filter-and-refinement framework. Table 4 shows the average query time of the six EMD computation methods for 32-NN similarity queries on the six datasets. SIA is the best method which constantly outperforms its base method SSP and other alternatives (e.g., TRA) by at least 2.4 times. In addition, SIA scales well with the problem dimensionality (i.e., the number of histogram bins and the cardinality of datasets). Figure 11 shows 

- 7http://ganymed.imib.rwth-aachen.de/irma 

> 8http://www.flickr.com 

> 9http://www.panoramio.com 

> 10http://www.image-net.org 

**Table 4: Comparison of black-box EMD computation methods** 

|||RETINA|IRMA|FLICKR|PANO.|FRIENDS|WORLD|
|---|---|---|---|---|---|---|---|
|Query time|CAP|0.68s|3.90s|7.89s|803s|3279s|22715s|
||COS|1.13s|6.48s|13.58s|1394s|5628s|48917s|
||NET|0.52s|4.13s|7.04s|763s|3573s|22774s|
||SSP|0.57s|6.14s|7.52s|2048s|10370s|65731s|
||TRA|0.57s|8.30s|7.72s|3395s|15307s|137414s|
||SIA|0.17s|1.51s|2.77s|318s|1362s|7082s|
|Filt|er time|0.006s|0.008s|0.749s|1.009s|1.476s|12.238s|



the performance of the methods as a function of _k_ on five datasets: RETINA, IRMA, PANORAMIO, FRIENDS, and WORLD.[11] SIA outperforms SSP by around an order of magnitude, while being at least two times faster than the runner-up network simplex (NET). Note that the relative performance difference between methods is not very sensitive to _k_ . SIA is obviously the best module for calculating EMD under the filter-and-refinement framework. Note also that the time spent in the filter phase (in Table 4) is negligible, which confirms our discussion that the _refinement phase dominates the runtime_ 

Next, we evaluate the improvement offered by our progressive bounding and dynamic refinement ordering techniques. Figure 12 compares the runtime of _k_ -NN queries when (i) using SIA as a black-box module, (ii) applying progressive bounding in SIA (PB), and (iii) applying dynamic refinement ordering in conjunction with progressive bounding in SIA (DRO). Observe that PB achieves a large performance improvement over SIA (i.e., the best black-box module in Figure 11). The improvement generally becomes more visible when the problem size increases (i.e., the number of bins and the cardinality of datasets). This can be explained by the fact that the size of the flow graph is quadratic to the number of histogram bins, therefore the latter iterations of SIA become extremely expensive. The progressive bounding technique helps to avoid reaching these iterations, as explained in Section 4.2. DRO offers a stable improvement over PB (40%–60%), indicating that the concurrent refinement and dynamic reordering techniques have positive impact on the performance. 

In summary, DRO is the recommended methodology for EMDbased similarity queries, being several times to two orders of magnitude faster than using off-the-shelf EMD computation methods. Notably, _all previous works_ [5,25,30,32] adopt _transportation simplex_ (TRA) for calculating EMD at the refinement phase. As shown in our evaluation, this method only performs well when the number of bins is relatively small due to its exponential time complexity. 

**Room for Improvement.** So far, we have shown the superiority of our PB and DRO techniques over existing approaches. To see how much room for improvement exists for EMD-based similarity queries, we compare PB and DRO to two ideal yet practically infeasible methods, ESS and OI. Assuming that we know the result of a _k_ -NN query by an oracle, ESS (Essential _k_ -NN search) calculates the EMDs of only the exact _k_ -NNs, representing the lowest possible effort to compute the results of a _k_ -NN query. OI (Oracle Index) assumes that an _oracle_ index is available which offers an optimal _getnext_ function that returns the objects in the ascending order of their _exact_ EMDs. OI can be viewed as an optimal ordering method integrated with the current state-of-the-art filtering techniques. In our experiments, both ESS and OI calculate EMDs by the best black-box module (SIA), and OI uses our progressive bounding (PB) technique to terminate EMD calculations early. 

Figure 13 shows the query time of four methods, PB, DRO, ESS, and OI, as a function of _k_ . First, we observe that DRO’s perfor- 

11The results on FLICKR are similar to those of RETINA. 

321 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0010-00.png'>
The image contains multiple charts and figures. Here's a description of the visual elements present:

### Figure 11: Performance of black-box EMD computation methods varying on \( k \)
This figure consists of five subplots labeled (a) RETINA, (b) IRMA, (c) PANORAMIO, (d) FRIENDS, and (e) WORLD. Each subplot is a line chart showing query time (in seconds) on the y-axis and \( k \) values (4, 8, 16, 32, 64) on the x-axis. The lines represent different methods: CAP, SSP, COS, SSP TRA, COS TRA, NET, and SIA. The query time is plotted on a logarithmic scale for subplots (c), (d), and (e).

### Figure 12: Performance of SIA, PB and DRO varying on \( k \)
This figure also consists of five subplots labeled (a) RETINA, (b) IRMA, (c) PANORAMIO, (d) FRIENDS, and (e) WORLD. Each subplot is a line chart showing query time (in seconds) on the y-axis and \( k \) values (4, 8, 16, 32, 64) on the x-axis. The lines represent different methods: SIA, PB, and DRO. The query time is plotted on a logarithmic scale for subplots (c), (d), and (e).

### Figure 13: Closeness of PB and DRO to the oracle methods (query time)
This figure consists of five subplots labeled (a) RETINA, (b) IRMA, (c) PANORAMIO, (d) FRIENDS, and (e) WORLD. Each subplot is a line chart showing query time (in seconds) on the y-axis and \( k \) values (4, 8, 16, 32, 64) on the x-axis. The lines represent different methods: PB, DRO, OI, and ESS. The query time is plotted on a logarithmic scale for subplots (c), (d), and (e).

### Additional Bar Charts
Below the figures, there are five bar charts labeled (a) RETINA, (b) IRMA, (c) PANORAMIO, (d) FRIENDS, and (e) WORLD. Each bar chart shows the number of refinements on the y-axis and \( k \) values (4, 8, 16, 32, 64) on the x-axis. The bars represent different methods: PB, DRO, OI, ESS, PB-C, and DRO-C. The number of refinements is plotted on a logarithmic scale for subplots (c), (d), and (e).
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
2.0 CAP SSP 15 CAP SSP 5 CAP SSP 20 CAP SSP 20 CAP SSP<br>COS TRA COS TRA COS TRA COS TRA COS TRA<br>1.5 NET SIA NET SIA 4 NET SIA 15 NET SIA 16 NET SIA<br>10<br>3 12<br>1.0 10<br>2 8<br>5<br>0.5 1 5 4<br>0.0 4 8 16 32 64 0 4 8 16 32 64 0 4 8 16 32 64 0 4 8 16 32 64 0 4 8 16 32 64<br>k k k k k<br>(a) RETINA (b) IRMA (c) PANORAMIO (d) FRIENDS (e) WORLD<br>Figure 11: Performance of black-box EMD computation methods varying on  k<br>0.3 SIA 3 SIA 0.5 SIA 2.0 SIA 10.0 SIA<br>PB PB PB PB PB<br>DRO DRO 0.4 DRO 1.5 DRO 8.0 DRO<br>0.2 2<br>0.3 60 150 6.0 600<br>0.1 1 0.2 4020 1.0 10050 4.0 400200<br>0.1 0 4 32 64 0.5 0 4 32 64 2.0 0 4 32 64<br>0.0 0 0.0 0.0 0.0<br>4 8 16 32 64 4 8 16 32 64 4 8 16 32 64 4 8 16 32 64 4 8 16 32 64<br>k k k k k<br>(a) RETINA (b) IRMA (c) PANORAMIO (d) FRIENDS (e) WORLD<br>Figure 12: Performance of SIA, PB and DRO varying on  k<br>0.25 PB 1.5 PB 80 PB 200 PB 750 PB<br>DRO DRO DRO DRO DRO<br>0.20 OIESS 1.0 OIESS 60 OIESS 150 OIESS 600 OIESS<br>0.15 450<br>40 100<br>0.10 300<br>0.5<br>0.05 20 50 150<br>0.00 4 8 16 32 64 0.0 4 8 16 32 64 0 4 8 16 32 64 0 4 8 16 32 64 0 4 8 16 32 64<br>k k k k k<br>(a) RETINA (b) IRMA (c) PANORAMIO (d) FRIENDS (e) WORLD<br>Figure 13: Closeness of PB and DRO to the oracle methods (query time)<br>300 PB 400 PB 3.0 PB 7.5 PB 12.0 PB<br>DRO DRO DRO DRO DRO<br>200 OIESSPB-CDRO-C 300 OIESSPB-CDRO-C 2.0 OIESSPB-CDRO-C 6.04.5 OIESSPB-CDRO-C 9.0 OIESSPB-CDRO-C<br>200 6.0<br>3.0<br>100 1.0<br>100 1.5 3.0<br>0 0 0 0 0<br>4 8 16 32 64 4 8 16 32 64 4 8 16 32 64 4 8 16 32 64 4 8 16 32 64<br>k k k k k<br>(a) RETINA (b) IRMA (c) PANORAMIO (d) FRIENDS (e) WORLD<br>Query time (s) Query time (s) 3s)10 3s)10 4s)10<br>Query time (x Query time (x Query time (x<br>Query time (s) Query time (s) 3s)10 3s)10 3s)10<br>Query time (x Query time (x Query time (x<br>Query time (s) Query time (s) Query time (s) Query time (s) Query time (s)<br>3)10 3)10 3)10<br># of refinements # of refinements # of refinements (x # of refinements (x # of refinements (x<br>**----- End of picture text -----**<br>


**Figure 14: Closeness of PB and DRO to the oracle methods (number of refinements)** 

mance is very close to that of OI, improving PB by a significant extent towards an ideal method. Figure 14 illustrates the number of EMD refinements[12] of these four methods, and also the number of _complete_ refinements (i.e., the EMD calculations that are fully conducted) of PB and DRO (denoted by PB-C and DRO-C respectively), varying on _k_ . These experiments confirm the robustness of our dynamic reordering technique as DRO commences almost the same number of EMDs compared to the optimal method OI. Besides, in Figure 14, PB-C and DRO-C are very close to ESS (i.e., _k_ ). In specific, DRO-C is only slightly larger than _k_ , indicating that only very few objects that are not the actual _k_ -NN results need to be fully refined by DRO, which again verifies the effectiveness of DRO. Obviously, there is limited room for improving DRO, using the current state-of-the-art filtering techniques, as its performance is already close to that of OI. On the other hand, we believe that there is still room for improving upon the current filtering methods as the performance gap between OI and ESS is still significant. 

12An object is counted even when only one path is augmented. 

## **5.2 Scalability Experiments** 

In the first scalability study, we conduct experiments on PANORAMIO subsets with cardinality 100K to 500K, on FRIENDS subsets (64K to 320K), and on WORLD subsets (0.6M to 3M), by randomly picking objects from the corresponding datasets. The lines in Figure 15 show the query time of three methods, SIA, PB, and DRO, as a function of the object cardinality, after setting _k_ = 32. PB and DRO scale very well with the database size (they are almost insensitive), since the progressive bounding technique benefits from better pruning thresholds owing to the increasing number of objects. This experiment exposes an important advantage of our approach: its performance is less sensitive to the database size, while _k_ is the main cost factor. Note that while the database size may increase arbitrarily, in practice _k_ is not expected to grow at the same rate, since similarity search queries typically retrieve a limited number of objects. The bars in Figure 15 show the number of refinements of SIA, PB, and DRO (note that in PB and DRO, only a portion of these are _complete refinements_ , denoted 

322 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0011-00.png'>
The image contains four bar charts and two line graphs. Here's a description of each:

### Bar Charts:
1. **(a) PANORAMIO**
   - **X-axis:** Dataset size (100K, 200K, 300K, 400K, 500K)
   - **Y-axis (left):** Query time (x10^-1 s)
   - **Y-axis (right):** Number of refinements (x10^1)
   - **Legend:** SIA, PB, PB-C, DRO, DRO-C
   - The chart shows query times and number of refinements for different dataset sizes.

2. **(b) FRIENDS**
   - **X-axis:** Dataset size (64K, 128K, 192K, 256K, 320K)
   - **Y-axis (left):** Query time (x10^-1 s)
   - **Y-axis (right):** Number of refinements (x10^1)
   - **Legend:** SIA, PB, PB-C, DRO, DRO-C
   - The chart shows query times and number of refinements for different dataset sizes.

3. **(c) WORLD**
   - **X-axis:** Dataset size (0.6M, 1.2M, 1.8M, 2.4M, 3.0M)
   - **Y-axis (left):** Query time (x10^-1 s)
   - **Y-axis (right):** Number of refinements (x10^1)
   - **Legend:** SIA, PB, PB-C, DRO, DRO-C
   - The chart shows query times and number of refinements for different dataset sizes.

### Line Graphs:
1. **(a) PANORAMIO**
   - **X-axis:** Number of bins (256, 400, 576, 784, 1024)
   - **Y-axis:** Query time (x10^-1 s)
   - **Legend:** SIA, PB, DRO
   - The graph shows the trend of query times with varying numbers of bins.

2. **(b) WORLD**
   - **X-axis:** Number of bins (576, 784, 1024, 1600, 2304)
   - **Y-axis:** Query time (x10^-1 s)
   - **Legend:** SIA, PB, DRO
   - The graph shows the trend of query times with varying numbers of bins.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
0.40.3 SIAPBDRO SIAPBDRO PB-CDRO-C 2 1.5 SIAPBDRO SIAPBDRO PB-CDRO-C 4 8.06.0 SIAPBDRO SIAPBDRO PB-CDRO-C 9 2.01.5 SIAPBDRO 68 SIAPBDRO<br>1.0 6<br>0.2 4.0 1.0 4<br>1<br>0.1 0.5 2 2.0 3 0.5 2<br>0.0 100K 200K 300K 400K 500K 0 0.0 64K 128K 192K 256K 320K 0 0 0.6M 1.2M 1.8M 2.4M 3.0M 0 0256 400 576 784 1024 0576784 1024 1600 2304<br>Dataset size Dataset size Dataset size Number of bins Number of bins<br>(a) PANORAMIO (b) FRIENDS (c) WORLD (a) PANORAMIO (b) WORLD<br>3s)10 3)10 3s)10 3)10 3s)10 3)10 3s)10 4s)10<br>Query time (x Query time (x Query time (x Query time (x Query time (x<br># of refinements (x # of refinements (x # of Refinements (x<br>**----- End of picture text -----**<br>


**Figure 15: Scalability to dataset cardinality (number of objects)** 

**Figure 16: Scalability to histogram dimensionality** 

by PB-C and DRO-C). We observe that SIA is quite sensitive to the number of refinements while PB and DRO are likely sensitive to the number of the complete refinements (PB-C and DRO-C). In addition, the improvement of DRO over PB is stable, indicating that the reordering technique is not affected by the increasing number of objects that survive the filters. 

In the second scalability study, we evaluate the effectiveness of our techniques against the histogram dimensionality (i.e., number of bins). We generate histogram sets of different dimensionalities (square grid granularities) up to 2304, on PANORAMIO and WORLD. Figure 16 shows the query time as a function of the histogram dimensionality on the two datasets ( _k_ = 32). We observe that the query time of PB and DRO increases more slowly compared to that of SIA. The graceful scalability of our methods w.r.t. histogram dimensionality enables the application of EMDbased similarity search on high-dimensional histogram representations (e.g., multi-dimensional features with fine partitioning). 

## **5.3 Parameter Tuning in DRO** 

Finally, we demonstrate the effect of two sensitive parameters in DRO, i.e., the maximum number of concurrently refined objects _b_ (the size of _PL_ ), and the function to prioritize objects in DRO. 




<IMAGE_CONTEXT src='document_processing/docs/outputs/extracted_images/earthmover/earthmover.pdf-0011-07.png'>
The image contains two line graphs labeled:

**(a) Size of \( PL, b \)**

**(b) Prioritizing function**

### **Graph (a)**
This graph displays query time in seconds (y-axis) against the size of \( PL, b \) (x-axis). Key observations:
- There are five data lines, each corresponding to a particular indexing value: 0.05%, 0.1%, 0.2%, and 0.4%.
- The x-axis ranges from approximately 4 to 64.
- The y-axis ranges from 0 to 60 seconds.
- All lines are upward-sloping, indicating that query time increases as \( PL, b \) increases.
- The graph's legend identifies each line by its corresponding label.

### **Graph (b)**
This graph also displays query time in seconds (y-axis) against another variable (x-axis). Observations:
- The graph shows multiple data lines corresponding to different prioritizing functions: PB, emd, emd\(^1\), and DRO.
- The x-axis ranges from approximately 4 to 64.
- The y-axis ranges from 0 to 80 seconds.
- The data lines are upward-sloping, indicating that query time increases with the variable.
- The graph's legend identifies the lines based on their respective prioritizing functions.
</IMAGE_CONTEXT>




**----- Start of picture text -----**<br>
60 0.05% 80 PB<br>0.1% emd [−]<br>40 0.2%0.4% 60 emdDRO [+]<br>40<br>20<br>20<br>0 4 8 16 32 64 0 4 8 16 32 64<br>k k<br>(a) Size of  PL ,  b (b) Prioritizing function<br>Query time (s) Query time (s)<br>**----- End of picture text -----**<br>


**Figure 17: Performance tuning of DRO on PANORAMIO** 

Figure 17(a) shows the average query time of _k_ -NN queries on the PANORAMIO dataset, for different values of _b_ (as different series). DRO becomes faster when _b_ increases, which indicates that concurrent refinement is an effective strategy to evaluate EMDbased _k_ -NN queries. On the other hand, as discussed in Section 4.4, the memory requirements of DRO are proportional to _b_ , so the performance improvement comes with a memory tradeoff. 

As mentioned in Section 4.4, the running lower bound _emd[−]_ can be used to prioritize objects in DRO. However, as shown in Figure 17(b), _emd[−]_ is not an effective prioritizing function since it does not take the bound tightness into consideration. For instance, assume that both _emd[−]_ **pa**[and] _[emd][−]_ **pb**[have][the][same][value.][Intu-] itively, if _emd_[+] **pa** _[<][emd]_[+] **pb**[,] **[p] a**[should][be][given][higher][priority] than **pb** during the refinement, because **pa** has a tighter bound and it is more likely to be added to the current _k_ -NN set _H_ and decrease _θ_ . Thus, DRO (in Figure 17(b) and the previous experiments) uses the following prioritizing function, which is a slight modification of _emd[−]_ (Definition 3): (1 _− α_ ) _·current cost_ + _α·estimated_ 

_cost_ , where _α_ indicates the tightness of the running bounds (i.e., _emdemd_[+] _−emd_[+] _[−]_ ). As Figure 17(b) shows, this function, when used in DRO, maintains a constant advantage over PB, compared to prioritizing by just using _emd[−]_ or _emd_[+] . 

## **6. RELATED WORK** 

Earth Mover’s Distance (EMD) was first introduced by the computer vision community as an effective similarity metric [23]. EMD is also known as Mallows distance or Wasserstein distance in statistics [15]. As a cross-bin distance, EMD matches better the human perception of differences [22], compared to bin-by-bin distances like Euclidean distance or _χ_[2] -statistic. EMD supports analysis and search in a wide range of application domains, such as image retrieval [23,24], computer vision [11,17,21], machine learning [6,9], probabilistic [25, 32] and multimedia databases [5, 30], video and music identification [28, 31], phishing detection [10], data cleaning [8], privacy [16], matrix factorization [26], clustering [4, 6], classification [14], etc. An empirical study [20] that compares nine families of image dissimilarity measures based on distributions of color and texture features shows that EMD has the best overall quality among the others, yet also the highest computational cost. 

Due to the usefulness of EMD, the database community developed techniques for similarity queries based on this measure. Work in this direction is based on the filter-and-refinement framework [5,25,30,32], described in Section 2.2. The main focus is the development of fast and effective lower bounds for EMD, which help in pruning objects that cannot make it in the result, at the filter phase. Assent et al. [5] were the first to study EMD in the filter-and-refinement framework. Wichterich et al. [30] propose a dimensionality reduction technique, showing that the EMD of two objects in the derived space is a lower bound for their actual EMD. Xu et al. [32] propose a lower bound of EMD based on primal-dual techniques [1] from linear programming and use B[+] -tree indexing to support the filter phase of _k_ -NN and range queries. Ruttenberg and Singh [25] develop a new index structure for EMD-based similarity queries based on the projection lower bound in [7]. All these solutions focus only on the effectiveness of filters and efficiency of the filter phase, simply treating the refinement phase as a black-box process. However, as we have shown in this paper, the refinement cost _dominates_ the overall cost and deserves more attention. 

Besides these results by the database community, there are also studies on efficient EMD approximations [2,3,13,19,27]. Andoni et al. [3] study EMD approximations in high-dimensional spaces. Pele and Werman [19] accelerates the EMD computation by limiting the number of edges in the flow graph, without guarantees of the quality of approximation. Both [13] and [27] study linear-time approximations of EMD, and [2] proposes sketches for approximating planar EMD. However, these works assume either specific ground distances (e.g., _L_ 1 norm) [2, 3, 27] and bin spaces (e.g., R[2] ) [2, 3, 13, 27], or certain histogram types (e.g., dominant color descriptor) [13], which do not apply to the general setup of EMD. 

323 

For example, the choice of ground distance could be applicationdependent [19, 22, 24]. Note that our proposed techniques do not have any of the above restrictions. Moreover, there is no study on filtering bounds and indexing structures on top of these approximation techniques. Therefore, using the approximation methods, a similarity query may have to compute EMDs between the query and all the objects in the database, which is not scalable for large datasets. Finally, the acceleration of EMD under Manhattan network when using _L_ 1 as the ground distance is studied in [18]. 

## **7. CONCLUSION** 

In this paper, we studied the efficient evaluation of similarity queries using Earth Mover’s Distance (EMD). First, we showed how we can adapt SIA, an algorithm originally proposed for spatial matching problems, to compute the EMD between two histograms efficiently. Then, we proposed a progressive refinement strategy, which updates a lower bound for EMD during its computation, in order to abandon early a partial EMD refinement, if the object cannot make it in the query result. Finally, we proposed a technique which concurrently handles the refinement of multiple candidates, by dynamically reordering them and computing upper bounds that help to tighten the pruning threshold early. Our experiments show that our methods are very effective in practice, decreasing the overall cost of EMD-based similarity queries by up to two orders of magnitude, compared to the state-of-the-art solution [25]. 

Note that although our discussion assumes that the histograms are normalized to sum up to the same values, EMD can also be applied in cases where histograms are not normalized (in this case, a slightly different definition than that of Equation 2 is used to reflect the maximum flow that could be sent from **q** to **p** ). In addition, it is not necessary that the two histograms have the same number or locations of bins. Our framework and solutions are not sensitive to these problem variants. Finally, note that our solution can also be used for evaluating _range_ similarity queries, where the objective is to retrieve objects whose EMD to **q** does not exceed a given threshold _ϵ_ . In this case, SIA and PB can directly be applied, however, DRO is not relevant because the threshold is fixed and insensitive to the execution order. 

In the future, we plan to study the optimization of the refinement step in similarity queries based on other expensive distance measures (such as dynamic time warping). 

## **8. ACKNOWLEDGMENT** 

This work is supported by grants HKU 714212E, 711110, and 711309E from Hong Kong RGC. Leong Hou U is supported by grant MYRG109(Y1-L3)-FST12-ULH. We would like to thank Brian Ruttenberg for providing part of his code on [25] and the anonymous reviewers for their insightful comments. 

## **9. REFERENCES** 

- [1] R. K. Ahuja, T. L. Magnanti, and J. B. Orlin. _Network flows: theory, algorithms and applications_ . Prentice Hall, 1993. 

- [2] A. Andoni, K. D. Ba, P. Indyk, and D. P. Woodruff. Efficient sketches for earth-mover distance, with applications. In _FOCS_ , pages 324–330, 2009. 

- [3] A. Andoni, P. Indyk, and R. Krauthgamer. Earth mover distance over high-dimensional spaces. In _SODA_ , pages 343–352, 2008. 

- [4] D. Applegate, T. Dasu, S. Krishnan, and S. Urbanek. Unsupervised clustering of multidimensional distributions using earth mover distance. In _KDD_ , pages 636–644, 2011. 

- [5] I. Assent, A. Wenning, and T. Seidl. Approximation techniques for indexing the earth mover’s distance in multimedia databases. In _ICDE_ , page 11, 2006. 

- [6] M. H. Coen, M. H. Ansari, and N. Fillmore. Comparing clusterings in space. In _ICML_ , pages 231–238, 2010. 

- [7] S. Cohen and L. Guibas. The earth mover”s distance: Lower bounds and invariance under translation. Technical report, Stanford University, 1997. 

- [8] T. Dasu and J. M. Loh. Statistical distortion: Consequences of data cleaning. _PVLDB_ , 5(11):1674–1683, 2012. 

- [9] N. Ferns, P. S. Castro, D. Precup, and P. Panangaden. Methods for computing state similarity in markov decision processes. In _UAI_ , pages 174–181, 2006. 

- [10] A. Y. Fu, L. Wenyin, and X. Deng. Detecting phishing web pages with visual similarity assessment based on earth mover’s distance (EMD). _IEEE Trans. Dependable Sec. Comput._ , 3(4):301–311, 2006. 

- [11] K. Grauman and T. Darrell. Fast contour matching using approximate earth mover’s distance. In _CVPR (1)_ , pages 220–227, 2004. 

- [12] F. S. Hillier and G. J. Lieberman. _Introduction to Mathematical Programming_ . McGraw-Hill, 1990. 

- [13] M.-H. Jang, S.-W. Kim, C. Faloutsos, and S. Park. A linear-time approximation of the earth mover’s distance. In _CIKM_ , pages 505–514, 2011. 

- [14] H. J. Karloff, S. Khot, A. Mehta, and Y. Rabani. On earthmover distance, metric labeling, and 0-extension. In _STOC_ , pages 547–556, 2006. 

- [15] E. Levina and P. J. Bickel. The earth mover’s distance is the mallows distance: Some insights from statistics. In _ICCV_ , pages 251–256, 2001. 

- [16] N. Li, T. Li, and S. Venkatasubramanian. t-closeness: Privacy beyond k-anonymity and l-diversity. In _ICDE_ , pages 106–115, 2007. 

- [17] P. Li, Q. Wang, and L. Zhang. A novel earth mover’s distance methodology for image matching with gaussian mixture models. In _ICCV_ , 2013 (to appear). 

- [18] H. Ling and K. Okada. An efficient earth mover’s distance algorithm for robust histogram comparison. _IEEE Trans. Pattern Anal. Mach. Intell._ , 29(5):840–853, 2007. 

- [19] O. Pele and M. Werman. Fast and robust earth mover’s distances. In _ICCV_ , pages 460–467, 2009. 

- [20] J. Puzicha, Y. Rubner, C. Tomasi, and J. M. Buhmann. Empirical evaluation of dissimilarity measures for color and texture. In _ICCV_ , pages 1165–1172, 1999. 

- [21] Z. Ren, J. Yuan, and Z. Zhang. Robust hand gesture recognition based on finger-earth mover’s distance with a commodity depth camera. In _ACM Multimedia_ , pages 1093–1096, 2011. 

- [22] Y. Rubner and C. Tomasi. _Perceptual Metrics for Image Database Navigation_ . Kluwer Academic Publishers, 2001. 

- [23] Y. Rubner, C. Tomasi, and L. J. Guibas. A metric for distributions with applications to image databases. In _ICCV_ , pages 59–66, 1998. 

- [24] Y. Rubner, C. Tomasi, and L. J. Guibas. The earth mover’s distance as a metric for image retrieval. _International Journal of Computer Vision_ , 40(2):99–121, 2000. 

- [25] B. E. Ruttenberg and A. K. Singh. Indexing the earth mover’s distance using normal distributions. _PVLDB_ , 5(3):205–216, 2011. 

- [26] R. Sandler and M. Lindenbaum. Nonnegative matrix factorization with earth mover’s distance metric. In _CVPR_ , pages 1873–1880, 2009. 

- [27] S. Shirdhonkar and D. W. Jacobs. Approximate earth mover’s distance in linear time. In _CVPR_ , pages 1–8, 2008. 

- [28] R. Typke, P. Giannopoulos, R. C. Veltkamp, F. Wiering, and R. van Oostrum. Using transportation distances for measuring melodic similarity. In _ISMIR_ , pages 107–114, 2003. 

- [29] L. H. U, K. Mouratidis, M. L. Yiu, and N. Mamoulis. Optimal matching between spatial datasets under capacity constraints. _ACM Trans. Database Syst._ , 35(2), 2010. 

- [30] M. Wichterich, I. Assent, P. Kranen, and T. Seidl. Efficient EMD-based similarity search in multimedia databases via flexible dimensionality reduction. In _SIGMOD_ , pages 199–212, 2008. 

- [31] J. Xu, Q. Bai, Y. Gu, A. K. H. Tung, G. Wang, G. Yu, and Z. Zhang. EUDEMON: A system for online video frame copy detection by earth mover’s distance. In _ICDE_ , pages 1233–1236, 2012. 

- [32] J. Xu, Z. Zhang, A. K. H. Tung, and G. Yu. Efficient and effective similarity search over probabilistic data based on earth mover’s distance. _PVLDB_ , 3(1):758–769, 2010. 

324 

