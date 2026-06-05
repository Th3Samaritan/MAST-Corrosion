import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool

class GalvanicCorrosionGNN(nn.Module):
    """
    Graph Neural Network for predicting corrosion rates across a multi-material assembly.
    Nodes = Parts (Materials)
    Edges = Joints (Physical/Electrolytic contacts)
    """
    def __init__(self, node_features, edge_features, hidden_dim):
        super(GalvanicCorrosionGNN, self).__init__()
        
        # Node embedding (e.g., standard EMF, surface area)
        self.node_embed = nn.Linear(node_features, hidden_dim)
        
        # Graph Convolutional Layers
        self.conv1 = GCNConv(hidden_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        
        # Edge/Joint prediction head (Predicts Galvanic Current Density per joint)
        self.edge_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_features, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1) # Output: Current Density i_corr
        )
        
        # Node prediction head (Predicts internal node potential V_node)
        self.node_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1) # Output: Operating Potential
        )

    def forward(self, x, edge_index, edge_attr, batch):
        # 1. Node feature embedding
        x = F.relu(self.node_embed(x))
        
        # 2. Message Passing
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        
        # 3. Predict Node Potentials
        v_nodes = self.node_predictor(x)
        
        # 4. Predict Edge Currents (Galvanic coupling)
        # Extract source and target node embeddings for each edge
        row, col = edge_index
        edge_features_combined = torch.cat([x[row], x[col], edge_attr], dim=1)
        i_edges = self.edge_predictor(edge_features_combined)
        
        return v_nodes, i_edges


def physics_informed_loss(v_nodes, i_edges_pred, i_edges_true, edge_index, lambda_physics=0.1):
    """
    Computes the loss incorporating both Data MSE and Physical constraints.
    """
    # 1. Data Loss: Mean Squared Error between predicted and true current densities
    loss_data = F.mse_loss(i_edges_pred, i_edges_true)
    
    # 2. Physics Loss A: Kirchhoff's Current Law (Conservation of Charge)
    # The sum of all galvanic currents entering/leaving a specific part must be zero 
    # (electrons produced by oxidation = electrons consumed by reduction)
    num_nodes = v_nodes.shape[0]
    node_net_currents = torch.zeros(num_nodes, device=v_nodes.device)
    
    row, col = edge_index
    # Add current to target node, subtract from source node
    node_net_currents.scatter_add_(0, col, i_edges_pred.squeeze())
    node_net_currents.scatter_add_(0, row, -i_edges_pred.squeeze())
    
    # Penalty for violating KCL (net current should be 0)
    loss_kcl = torch.mean(node_net_currents ** 2)
    
    # 3. Physics Loss B: Potential Gradient Rule
    # Current should flow from the more negative potential (Anode) to positive (Cathode).
    # If the network predicts current flowing backward against the potential gradient, penalize it.
    v_source = v_nodes[row]
    v_target = v_nodes[col]
    delta_v = v_target - v_source
    
    # If delta_v and i_edge have opposite signs, their product is negative.
    # We penalize negative products (current flowing against thermodynamics).
    thermo_violation = F.relu(-(delta_v * i_edges_pred)) 
    loss_thermo = torch.mean(thermo_violation)
    
    # Total Loss
    total_loss = loss_data + lambda_physics * (loss_kcl + loss_thermo)
    
    return total_loss, loss_data, loss_kcl, loss_thermo

# Example Usage Block (Mock Data)
if __name__ == "__main__":
    print("Initializing PINN Architecture...")
    
    # Mock parameters
    num_nodes = 5    # e.g., 5 parts in the assembly
    num_edges = 6    # e.g., 6 joints between parts
    node_feat_dim = 2 # e.g., [Standard_EMF, Surface_Area]
    edge_feat_dim = 2 # e.g., [Conductivity, Contact_Area]
    
    model = GalvanicCorrosionGNN(node_features=node_feat_dim, edge_features=edge_feat_dim, hidden_dim=32)
    
    # Mock inputs
    x = torch.randn((num_nodes, node_feat_dim))
    edge_index = torch.tensor([[0, 1, 1, 2, 3, 4], [1, 0, 2, 1, 4, 3]], dtype=torch.long)
    edge_attr = torch.randn((num_edges, edge_feat_dim))
    batch = torch.zeros(num_nodes, dtype=torch.long)
    i_edges_true = torch.randn((num_edges, 1)) # Ground truth from dataset
    
    # Forward pass
    v_nodes, i_edges_pred = model(x, edge_index, edge_attr, batch)
    
    # Calculate Loss
    loss, l_data, l_kcl, l_thermo = physics_informed_loss(v_nodes, i_edges_pred, i_edges_true, edge_index)
    
    print(f"Total Loss: {loss.item():.4f}")
    print(f"  ├─ Data MSE Loss: {l_data.item():.4f}")
    print(f"  ├─ KCL Physics Penalty: {l_kcl.item():.4f}")
    print(f"  └─ Thermodynamic Penalty: {l_thermo.item():.4f}")