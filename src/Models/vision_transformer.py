import torch
import torch.nn as nn
import torch.nn.functional as F

class PatchEmbedding(nn.Module):
    def __init__(self, image_size, patch_size, in_channels, embed_dim):
        super(PatchEmbedding, self).__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.in_channels = in_channels
        self.embed_dim = embed_dim
        self.num_patches = (image_size // patch_size) ** 2
        self.projection = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        x = self.projection(x)  # (B, C, H, W) -> (B, E, H', W')
        B, E, H, W = x.shape
        x = x.permute(0, 2, 3, 1)  # (B, E, H', W') -> (B, H', W', E)
        x = x.view(B, H * W, E)  # (B, H', W', E) -> (B, N, E), where N = H' * W'
        return x

class MultiHeadAttention(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super(MultiHeadAttention, self).__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5
        self.query = nn.Linear(embed_dim, embed_dim)
        self.key = nn.Linear(embed_dim, embed_dim)
        self.value = nn.Linear(embed_dim, embed_dim)
        self.fc_out = nn.Linear(embed_dim, embed_dim)

    def forward(self, query, key, value, mask=None):
        B, N, _ = query.shape
        query = self.query(query).view(B, N, self.num_heads, self.head_dim).permute(0, 2, 1, 3)
        key = self.key(key).view(B, N, self.num_heads, self.head_dim).permute(0, 2, 1, 3)
        value = self.value(value).view(B, N, self.num_heads, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.matmul(query, key.transpose(-2, -1)) * self.scale
        if mask is not None:
            scores += mask.unsqueeze(1).unsqueeze(1)  # Broadcasting

        attention_weights = F.softmax(scores, dim=-1)
        out = torch.matmul(attention_weights, value)
        out = out.permute(0, 2, 1, 3).contiguous().view(B, N, self.embed_dim)
        out = self.fc_out(out)
        return out, attention_weights

class FeedForward(nn.Module):
    def __init__(self, embed_dim, hidden_dim):
        super(FeedForward, self).__init__()
        self.linear1 = nn.Linear(embed_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, embed_dim)

    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = self.linear2(x)
        return x

class TransformerEncoderLayer(nn.Module):
    def __init__(self, embed_dim, num_heads, hidden_dim, dropout):
        super(TransformerEncoderLayer, self).__init__()
        self.attention = MultiHeadAttention(embed_dim, num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.feed_forward = FeedForward(embed_dim, hidden_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        residual = x
        x = self.norm1(x + self.dropout(self.attention(x, x, x, mask)[0]))
        x = self.norm2(x + self.dropout(self.feed_forward(x)))
        return x

class VisionTransformer(nn.Module):
    def __init__(self, image_size, patch_size, in_channels, num_classes, embed_dim, num_heads, hidden_dim, num_layers, dropout):
        super(VisionTransformer, self).__init__()
        self.patch_embed = PatchEmbedding(image_size, patch_size, in_channels, embed_dim)
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim))
        num_patches = (image_size // patch_size) ** 2
        self.pos_embed = nn.Parameter(torch.randn(1, num_patches + 1, embed_dim))  # Adjusted positional embedding
        self.dropout = nn.Dropout(dropout)
        self.transformer_encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(embed_dim, num_heads, hidden_dim, dropout) for _ in range(num_layers)
        ])
        self.layer_norm = nn.LayerNorm(embed_dim)
        self.fc = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]
        x = self.patch_embed(x)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = x + self.pos_embed[:, :x.shape[1]]  # Adjusted positional embedding based on input size
        x = self.dropout(x)
        
        for layer in self.transformer_encoder_layers:
            x = layer(x)
        
        x = self.layer_norm(x[:, 0])
        x = self.fc(x)
        return x