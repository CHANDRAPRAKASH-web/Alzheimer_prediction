from dataloader import train_loader

images, labels = next(iter(train_loader))

print("=" * 50)

print("Batch Shape :", images.shape)

print("Labels Shape :", labels.shape)

print("Labels :", labels)

print("=" * 50)