from custom_neat_lib.graphs import feed_forward_layers
from custom_neat_lib.six_util import itervalues
import numpy as np


class FeedForwardNetwork(object):
    def __init__(self, inputs, outputs, node_evals):
        self.input_nodes = list(inputs)
        self.output_nodes = list(outputs)
        self.node_evals = node_evals
        self.values = dict((key, 0.0) for key in inputs + outputs)

        # Pre-compile vectorized NumPy execution structures
        all_keys = list(inputs)
        for k in outputs:
            if k not in all_keys:
                all_keys.append(k)
        for node, _, _, _, _, links in node_evals:
            if node not in all_keys:
                all_keys.append(node)
            for i, _ in links:
                if i not in all_keys:
                    all_keys.append(i)

        self.key_to_idx = {k: idx for idx, k in enumerate(all_keys)}
        self.n_total = len(all_keys)
        self.n_inputs = len(inputs)
        self.output_indices = [self.key_to_idx[k] for k in outputs]

        self._vectorized_evals = []
        for node, act, agg, bias, resp, links in node_evals:
            node_idx = self.key_to_idx[node]
            src_indices = np.array([self.key_to_idx[i] for i, _ in links], dtype=np.int32)
            eff_weights = np.array([float(w * resp) for _, w in links], dtype=np.float64)
            self._vectorized_evals.append((node_idx, float(bias), eff_weights, src_indices, act))

        # Fast path: single direct output node connected solely to input nodes
        self._is_single_direct = False
        if len(self.output_indices) == 1 and len(self._vectorized_evals) == 1:
            node_idx, bias, eff_weights, src_indices, act = self._vectorized_evals[0]
            if node_idx == self.output_indices[0] and (len(src_indices) == 0 or np.all(src_indices < self.n_inputs)):
                self._is_single_direct = True
                self._dense_weights = np.zeros(self.n_inputs, dtype=np.float64)
                if len(src_indices) > 0:
                    self._dense_weights[src_indices] = eff_weights
                self._single_bias = bias
                self._single_act = act

        self._vals = np.zeros(self.n_total, dtype=np.float64)

    def activate(self, inputs):
        if len(self.input_nodes) != len(inputs):
            raise RuntimeError("Expected {0:n} inputs, got {1:n}".format(len(self.input_nodes), len(inputs)))

        if self._is_single_direct:
            s = np.dot(self._dense_weights, inputs)
            return [float(self._single_act(self._single_bias + s))]

        vals = self._vals
        vals[:self.n_inputs] = inputs
        for node_idx, bias, weights, src_indices, act_func in self._vectorized_evals:
            s = np.dot(weights, vals[src_indices])
            vals[node_idx] = act_func(bias + s)

        return [float(vals[i]) for i in self.output_indices]

    def __getstate__(self):
        return {
            'input_nodes': self.input_nodes,
            'output_nodes': self.output_nodes,
            'node_evals': self.node_evals
        }

    def __setstate__(self, state):
        self.__init__(state['input_nodes'], state['output_nodes'], state['node_evals'])

    @staticmethod
    def create(genome, config):
        """ Receives a genome and returns its phenotype (a FeedForwardNetwork). """

        # Gather expressed connections.
        connections = [cg.key for cg in itervalues(genome.connections) if cg.enabled]

        layers = feed_forward_layers(config.genome_config.input_keys, config.genome_config.output_keys, connections)
        node_evals = []
        for layer in layers:
            for node in layer:
                inputs = []
                node_expr = [] # currently unused
                for conn_key in connections:
                    inode, onode = conn_key
                    if onode == node:
                        cg = genome.connections[conn_key]
                        inputs.append((inode, cg.weight))
                        node_expr.append("v[{}] * {:.7e}".format(inode, cg.weight))


                ng = genome.nodes[node]
                aggregation_function = config.genome_config.aggregation_function_defs.get(ng.aggregation)
                activation_function = config.genome_config.activation_defs.get(ng.activation)
                node_evals.append((node, activation_function, aggregation_function, ng.bias, ng.response, inputs))

        return FeedForwardNetwork(config.genome_config.input_keys, config.genome_config.output_keys, node_evals)


