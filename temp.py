import Levenshtein

str1 = "1247"
str2 = "1226"
distance = Levenshtein.distance(str1, str2)
print(f"Расстояние Левенштейна: {distance}")  # Выведет: 1