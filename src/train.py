import torch
from torch.utils.tensorboard import SummaryWriter
from src.helper import accuracy_fn
from tqdm import tqdm

class Train(object):
    def __init__(
        self,
        model: torch.nn.Module,
        train_loader: torch.utils.data.DataLoader,
        test_loader: torch.utils.data.DataLoader,
        loss_fn: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        device: torch.device,
    ):
        self.model = model
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.device = device
        self.writer = SummaryWriter()  # Initialize TensorBoard writer

    def train_step(self, epoch):
        train_loss, train_acc = 0, 0
        self.model.train()  # Put model on training mode

        for batch, (X, y) in enumerate(self.train_loader):
            X, y = X.to(self.device), y.to(self.device)

            y_pred = self.model(X)

            # Calculate loss
            loss = self.loss_fn(y_pred, y)
            train_loss += loss.item()
            train_acc += accuracy_fn(y_true=y, y_pred=y_pred.argmax(dim=1))
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        train_loss /= len(self.train_loader)
        train_acc /= len(self.train_loader)

        # Write to TensorBoard
        self.writer.add_scalar('Loss/train', train_loss, epoch)
        self.writer.add_scalar('Accuracy/train', train_acc, epoch)

        print(f'Train Epoch {epoch}: Loss: {train_loss:.5f} | Accuracy: {train_acc:.2f}')

    def test_step(self, epoch):
        test_loss, test_acc = 0, 0
        self.model.eval()  # Put model on evaluation mode

        with torch.no_grad():
            for X, y in self.test_loader:
                X, y = X.to(self.device), y.to(self.device)

                test_pred = self.model(X)

                test_loss += self.loss_fn(test_pred, y).item()
                test_acc += accuracy_fn(y_true=y, y_pred=test_pred.argmax(dim=1))

            test_loss /= len(self.test_loader)
            test_acc /= len(self.test_loader)

            # Write to TensorBoard
            self.writer.add_scalar('Loss/test', test_loss, epoch)
            self.writer.add_scalar('Accuracy/test', test_acc, epoch)

            print(f'Test Epoch {epoch}: Loss: {test_loss:.5f} | Accuracy: {test_acc:.2f}')

    def train(self, num_epochs):
        for epoch in range(1, num_epochs + 1):
            self.train_step(epoch)
            self.test_step(epoch)

        self.writer.close()  # Close TensorBoard writer after training