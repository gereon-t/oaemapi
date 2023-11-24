import pandas as pd
import matplotlib.pyplot as plt


data = pd.read_csv("oaem-export/oaems-2023-08-01-003.csv", header=None)


plt.figure(figsize=(10, 5))
plt.axis("equal")
plt.plot(data.iloc[:, 0], data.iloc[:, 1], "k-")

plt.show()
