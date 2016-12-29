from landlab.components.flow_director.flow_director_to_one import FlowDirectorToOne
from landlab.components.flow_director import flow_direction_DN
from landlab import FIXED_VALUE_BOUNDARY, FIXED_GRADIENT_BOUNDARY
from landlab import VoronoiDelaunayGrid

import numpy

class FlowDirectorSteepestDescent(FlowDirectorToOne):
    """Single-path (steepest direction) flow direction finding on irregular 
     grids
     
     This method is not implemented for raster grids. Use either FlowDirectorD8
     or FlowDirectorD4 instead. 

    Stores as ModelGrid fields:
        
        -  Node array of receivers (nodes that receive flow), or ITS OWN ID if
           there is no receiver: *'flow__receiver_node'*
        -  Node array of steepest downhill slopes:
           *'topographic__steepest_slope'*
        -  Node array containing ID of link that leads from each node to its
           receiver, or BAD_INDEX_VALUE if no link:
           *'flow__link_to_receiver_node'*
        -  Boolean node array of all local lows: *'flow__sink_flag'*
        
       
    The primary method of this class is :func:`run_one_step`.

    Construction::

        FlowDirectorSteepestDescent(grid, surface='topographic__elevation')

    Parameters
    ----------
    grid : ModelGrid
        A grid of type VoronoiDelaunayGrid.
    surface : field name at node or array of length node, optional
        The surface to direct flow across, default is field at node: 
        topographic__elevation,.   
  
   
    Examples
    --------
    >>> import numpy as np
    
    For the example we will use a Hexagonal Model Grid, a special type of 
    Voroni Grid that has regularly spaced hexagonal cells. 
    
    >>> from landlab import HexModelGrid
    >>> from landlab.components import FlowDirectorSteepestDescent
    >>> mg = HexModelGrid(5,3)
    >>> _ = mg.add_field('topographic__elevation', mg.node_x + np.round(mg.node_y), at = 'node')
    >>> fd=FlowDirectorSteepestDescent(mg, 'topographic__elevation')
    >>> fd.elevs
    array([ 0. ,  1. ,  2. ,  
        0.5,  1.5,  2.5,  3.5,  
      1. ,  2. ,  3. ,  4. , 5. ,
        2.5,  3.5,  4.5,  5.5,  
            3. ,  4. ,  5. ])
    >>> fd.run_one_step()
    >>> mg.at_node['flow__receiver_node']
    array([ 0,  1,  2,  
          3,  0,  1,  6,  
        7,  3,  4,  5,  11, 
          12,  8,  9, 15, 
            16, 17, 18])
    >>> mg.at_node['topographic__steepest_slope']
    array([ 0. ,  0. ,  0. ,  
        0. ,  1.5,  1.5,   0. ,  
      0. ,  1.5,  1.5,  1.5,  0. , 
        0. ,  1.5,  1.5,  0. ,  
            0. ,  0. ,  0. ])
    >>> mg.at_node['flow__link_to_receiver_node']
    array([-1, -1, -1, 
         -1,  3,  5, -1, 
       -1, 12, 14, 16, -1, 
         -1, 25, 27, -1, 
           -1, -1, -1])
    >>> mg.at_node['flow__sink_flag']
    array([1, 1, 1,
          1, 0, 0, 1, 
         1, 0, 0, 0, 1,
          1, 0, 0, 1, 
            1, 1, 1], dtype=int8)
    """

    _name = 'FlowDirectorSteepestDescent'

    def __init__(self, grid, surface='topographic__elevation'):
        super(FlowDirectorSteepestDescent, self).__init__(grid, surface)
        self._is_Voroni = isinstance(self._grid, VoronoiDelaunayGrid)
        if not self._is_Voroni:
            raise NotImplementedError('FlowDirectorSteepestDescent not implemented for grids, use FlowDirectorD4 or FlowDirectorD8 instead.')
        
        self.method = 'SteepestDescent'
       
    def run_one_step(self):   
        
        # step 0. Check and update BCs
        if self._bc_set_code != self.grid.bc_set_code:
            self.updated_boundary_conditions()
            self._bc_set_code = self.grid.bc_set_code           
        
        # step 1. Calculate link slopes. 
        link_slope = - self._grid.calc_grad_of_active_link(
                self.elevs)
                
        # Step 2. Find and save base level nodes. 
        (baselevel_nodes, ) = numpy.where(
            numpy.logical_or(self._grid.status_at_node == FIXED_VALUE_BOUNDARY,
                             self._grid.status_at_node == FIXED_GRADIENT_BOUNDARY))
                   
        
        # Calculate flow directions      
        receiver, steepest_slope, sink, recvr_link = \
        flow_direction_DN.flow_directions(self.elevs, self._active_links,
                                     self._activelink_tail,
                                     self._activelink_head, link_slope,
                                     grid=self._grid,
                                     baselevel_nodes=baselevel_nodes)
        self.sink = sink
        
       # Save the four ouputs of this component.                                  
        self._grid['node']['flow__receiver_node'][:] = receiver
        self._grid['node']['topographic__steepest_slope'][:] = steepest_slope
        self._grid['node']['flow__link_to_receiver_node'][:] = recvr_link
        self._grid['node']['flow__sink_flag'][:] = numpy.zeros_like(receiver,
                                                                    dtype=bool)
        self._grid['node']['flow__sink_flag'][sink] = True
    
        
if __name__ == '__main__':
    import doctest
    doctest.testmod()