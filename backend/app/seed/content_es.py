"""Seed content: Spanish for English speakers.

Content is authored as vocabulary + sentences per lesson; `builder.py` turns each lesson into a
varied sequence of the five exercise types. Every word and sentence is tagged with concepts so the
learner model and the tutor agents can reason about *what* a learner is struggling with.

Sentence fields:
    es      accepted Spanish answers (first = canonical)
    en      accepted English answers (first = canonical)
    c       concept keys
    blank   (word_to_blank, [distractors]) for fill-in-the-blank, optional
"""

CONCEPTS = [
    ("vocab.basics", "Greetings & basics", "vocab",
     "Short everyday words: hola, adiós, gracias, por favor, sí, no."),
    ("vocab.food", "Food & drink", "vocab", "Food words almost always come with an article: el pan, la leche."),
    ("vocab.people", "People", "vocab", "niño/niña, hombre/mujer: many people-words flip -o/-a for gender."),
    ("vocab.animals", "Animals", "vocab", "el gato, el perro, la vaca. Learn each animal together with its article."),
    ("vocab.family", "Family", "vocab", "madre/padre, hermano/hermana. 'mi' = my, before any noun."),
    ("vocab.places", "Places", "vocab", "la casa, la escuela, la ciudad. Words ending in -dad are feminine."),
    ("grammar.gender_articles", "Gender & articles (el/la, un/una)", "grammar",
     "Every noun is masculine or feminine. -o words are usually masculine (el/un), -a words usually "
     "feminine (la/una). Exceptions to remember: el agua, el día, la mano. -e words must be memorised: "
     "el hombre, la leche."),
    ("grammar.plurals", "Plurals (los/las)", "grammar",
     "Add -s after a vowel and -es after a consonant. el gato → los gatos, la mujer → las mujeres."),
    ("grammar.subject_pronouns", "Subject pronouns", "grammar",
     "yo (I), tú (you), él (he), ella (she), nosotros (we). The accent matters: tú = you, tu = your; "
     "él = he, el = the."),
    ("grammar.adjective_agreement", "Adjective agreement", "grammar",
     "Adjectives match the noun: el gato pequeño, la niña pequeña, los perros grandes."),
    ("grammar.word_order", "Questions & negation", "grammar",
     "Put 'no' right before the verb: No tengo un perro. Questions open with ¿ and question words "
     "carry an accent: qué, dónde, cómo, quién."),
    ("verb.ser", "The verb ser (to be)", "verb", "soy, eres, es, somos, son. Use ser for who/what someone is."),
    ("verb.comer_beber", "Present tense -er verbs", "verb",
     "comer → como, comes, come, comemos, comen. beber → bebo, bebes, bebe..."),
    ("verb.tener", "The verb tener (to have)", "verb", "tengo, tienes, tiene, tenemos, tienen. Irregular!"),
    ("spelling.accents", "Accents & ñ", "spelling",
     "Accents change meaning and pronunciation: adiós, café, tú, él, niño, araña."),
]

G = "grammar.gender_articles"
PRON = "grammar.subject_pronouns"
ACC = "spelling.accents"

COURSE = {
    "slug": "es-en",
    "title": "Spanish",
    "from_lang": "en",
    "to_lang": "es",
    "flag": "🇪🇸",
    "units": [
        {
            "title": "Order in a café, greet people",
            "description": "Use basic phrases, food words and el/la",
            "color": "#7C5CFF",
            "guidebook": [
                {"es": "Hola, buenos días", "en": "Hello, good morning"},
                {"es": "Un café, por favor", "en": "A coffee, please"},
                {"es": "El niño come una manzana", "en": "The boy eats an apple"},
            ],
            "skills": [
                {
                    "title": "Greetings", "icon": "👋", "concepts": ["vocab.basics"],
                    "lessons": [
                        {
                            "words": [("hola", "hello", "👋", []), ("adiós", "goodbye", "🙋", [ACC]),
                                      ("gracias", "thank you", "🙏", []), ("por favor", "please", "🥺", [])],
                            "sentences": [
                                {"es": ["Hola, gracias"], "en": ["Hello, thank you", "Hi, thank you", "Hello, thanks", "Hi, thanks"], "c": []},
                                {"es": ["Gracias, adiós"], "en": ["Thank you, goodbye", "Thanks, goodbye", "Thank you, bye", "Thanks, bye"], "c": [ACC]},
                                {"es": ["Hola, por favor"], "en": ["Hello, please", "Hi, please"], "c": []},
                            ],
                        },
                        {
                            "words": [("sí", "yes", "✅", [ACC]), ("no", "no", "❌", []),
                                      ("buenos días", "good morning", "🌅", []), ("buenas noches", "good night", "🌙", [])],
                            "sentences": [
                                {"es": ["Sí, por favor"], "en": ["Yes, please"], "c": [ACC]},
                                {"es": ["No, gracias"], "en": ["No, thank you", "No, thanks"], "c": []},
                                {"es": ["Hola, buenos días"], "en": ["Hello, good morning", "Hi, good morning"], "c": []},
                                {"es": ["Adiós, buenas noches"], "en": ["Goodbye, good night", "Bye, good night"], "c": [ACC]},
                            ],
                        },
                    ],
                },
                {
                    "title": "Food", "icon": "🍎", "concepts": ["vocab.food", G],
                    "lessons": [
                        {
                            "words": [("el agua", "the water", "💧", [G]), ("el pan", "the bread", "🍞", [G]),
                                      ("la manzana", "the apple", "🍎", [G]), ("la leche", "the milk", "🥛", [G])],
                            "sentences": [
                                {"es": ["El pan y el agua"], "en": ["The bread and the water"], "c": [G], "blank": ("El", ["La", "Los"])},
                                {"es": ["La manzana, por favor"], "en": ["The apple, please"], "c": [G], "blank": ("La", ["El", "Las"])},
                                {"es": ["La leche y el pan"], "en": ["The milk and the bread"], "c": [G], "blank": ("leche", ["agua", "manzana"])},
                            ],
                        },
                        {
                            "words": [("el café", "the coffee", "☕", [G, ACC]), ("el queso", "the cheese", "🧀", [G]),
                                      ("la naranja", "the orange", "🍊", [G]), ("el arroz", "the rice", "🍚", [G])],
                            "sentences": [
                                {"es": ["Un café, por favor"], "en": ["A coffee, please", "One coffee, please"], "c": [G, ACC], "blank": ("Un", ["Una", "La"])},
                                {"es": ["Una manzana y una naranja"], "en": ["An apple and an orange"], "c": [G], "blank": ("Una", ["Un", "El"])},
                                {"es": ["El queso y el arroz"], "en": ["The cheese and the rice"], "c": [G], "blank": ("arroz", ["agua", "naranja"])},
                                {"es": ["El café y la leche"], "en": ["The coffee and the milk"], "c": [G, ACC]},
                            ],
                        },
                        {
                            "words": [("la sopa", "the soup", "🍲", [G]), ("el huevo", "the egg", "🥚", [G]),
                                      ("la carne", "the meat", "🥩", [G])],
                            "sentences": [
                                {"es": ["Un huevo y una manzana"], "en": ["An egg and an apple", "One egg and one apple"], "c": [G], "blank": ("Un", ["Una", "La"])},
                                {"es": ["La sopa y el pan"], "en": ["The soup and the bread"], "c": [G], "blank": ("La", ["El", "Un"])},
                                {"es": ["La carne, por favor"], "en": ["The meat, please"], "c": [G], "blank": ("La", ["El", "Los"])},
                            ],
                        },
                    ],
                },
                {
                    "title": "People", "icon": "🧒", "concepts": ["vocab.people", G, PRON, "verb.ser"],
                    "lessons": [
                        {
                            "words": [("el niño", "the boy", "👦", [G, ACC]), ("la niña", "the girl", "👧", [G, ACC]),
                                      ("el hombre", "the man", "👨", [G]), ("la mujer", "the woman", "👩", [G])],
                            "sentences": [
                                {"es": ["El niño y la niña"], "en": ["The boy and the girl"], "c": [G, ACC], "blank": ("la", ["el", "los"])},
                                {"es": ["Yo soy una mujer", "Soy una mujer"], "en": ["I am a woman"], "c": [G, "verb.ser"], "blank": ("una", ["un", "el"])},
                                {"es": ["Yo soy un hombre", "Soy un hombre"], "en": ["I am a man"], "c": [G, "verb.ser"], "blank": ("un", ["una", "la"])},
                            ],
                        },
                        {
                            "words": [("yo", "I", "🙋", [PRON]), ("tú", "you", "🫵", [PRON, ACC]),
                                      ("él", "he", "👨", [PRON, ACC]), ("ella", "she", "👩", [PRON])],
                            "sentences": [
                                {"es": ["Él es un niño"], "en": ["He is a boy"], "c": [PRON, "verb.ser", ACC], "blank": ("es", ["eres", "soy"])},
                                {"es": ["Ella es una mujer"], "en": ["She is a woman"], "c": [PRON, "verb.ser", G], "blank": ("una", ["un", "el"])},
                                {"es": ["Tú eres una niña"], "en": ["You are a girl"], "c": [PRON, "verb.ser", ACC], "blank": ("eres", ["es", "soy"])},
                                {"es": ["Yo soy Ana", "Soy Ana"], "en": ["I am Ana"], "c": [PRON, "verb.ser"], "blank": ("soy", ["es", "eres"])},
                            ],
                        },
                    ],
                },
                {"kind": "chest", "title": "Treasure", "icon": "🎁"},
                {
                    "title": "Eat & drink", "icon": "🍽️", "concepts": ["verb.comer_beber", "vocab.food"],
                    "lessons": [
                        {
                            "words": [("como", "I eat", "🍽️", ["verb.comer_beber"]), ("bebo", "I drink", "🥤", ["verb.comer_beber"]),
                                      ("come", "he eats", "😋", ["verb.comer_beber"]), ("bebe", "she drinks", "🧃", ["verb.comer_beber"])],
                            "sentences": [
                                {"es": ["Yo como pan", "Como pan"], "en": ["I eat bread", "I am eating bread"], "c": ["verb.comer_beber"], "blank": ("como", ["come", "comes"])},
                                {"es": ["Yo bebo agua", "Bebo agua"], "en": ["I drink water", "I am drinking water"], "c": ["verb.comer_beber"], "blank": ("bebo", ["bebe", "bebes"])},
                                {"es": ["El niño come una manzana"], "en": ["The boy eats an apple", "The boy is eating an apple"], "c": ["verb.comer_beber", G], "blank": ("come", ["como", "comes"])},
                                {"es": ["La mujer bebe leche"], "en": ["The woman drinks milk", "The woman is drinking milk"], "c": ["verb.comer_beber"], "blank": ("bebe", ["bebo", "bebes"])},
                            ],
                        },
                        {
                            "words": [("comes", "you eat", "🍴", ["verb.comer_beber"]), ("bebes", "you drink", "🍵", ["verb.comer_beber"])],
                            "sentences": [
                                {"es": ["Tú comes queso", "Comes queso"], "en": ["You eat cheese", "You are eating cheese"], "c": ["verb.comer_beber", ACC], "blank": ("comes", ["como", "come"])},
                                {"es": ["Ella bebe café"], "en": ["She drinks coffee", "She is drinking coffee"], "c": ["verb.comer_beber", ACC], "blank": ("bebe", ["bebo", "bebes"])},
                                {"es": ["Él come arroz"], "en": ["He eats rice", "He is eating rice"], "c": ["verb.comer_beber", ACC], "blank": ("come", ["como", "comes"])},
                                {"es": ["¿Tú bebes leche?", "¿Bebes leche?"], "en": ["Do you drink milk?", "Are you drinking milk?"], "c": ["verb.comer_beber", ACC], "blank": ("bebes", ["bebo", "bebe"])},
                            ],
                        },
                    ],
                },
                {"kind": "trophy", "title": "Unit 1 review", "icon": "🏆"},
            ],
        },
        {
            "title": "Describe people and animals",
            "description": "Use ser, adjectives and plurals",
            "color": "#B157E8",
            "guidebook": [
                {"es": "El gato es pequeño", "en": "The cat is small"},
                {"es": "Nosotros somos amigos", "en": "We are friends"},
                {"es": "Los perros son grandes", "en": "The dogs are big"},
            ],
            "skills": [
                {
                    "title": "Animals", "icon": "🐱", "concepts": ["vocab.animals", G],
                    "lessons": [
                        {
                            "words": [("el gato", "the cat", "🐱", [G]), ("el perro", "the dog", "🐶", [G]),
                                      ("el pájaro", "the bird", "🐦", [G, ACC]), ("el caballo", "the horse", "🐴", [G])],
                            "sentences": [
                                {"es": ["El gato come"], "en": ["The cat eats", "The cat is eating"], "c": [G, "verb.comer_beber"], "blank": ("El", ["La", "Los"])},
                                {"es": ["El perro bebe agua"], "en": ["The dog drinks water", "The dog is drinking water"], "c": [G, "verb.comer_beber"], "blank": ("bebe", ["bebo", "bebes"])},
                                {"es": ["Un pájaro y un gato"], "en": ["A bird and a cat"], "c": [G, ACC], "blank": ("un", ["una", "la"])},
                            ],
                        },
                        {
                            "words": [("la vaca", "the cow", "🐄", [G]), ("el pez", "the fish", "🐟", [G]),
                                      ("la araña", "the spider", "🕷️", [G, ACC]), ("el oso", "the bear", "🐻", [G])],
                            "sentences": [
                                {"es": ["La vaca bebe agua"], "en": ["The cow drinks water", "The cow is drinking water"], "c": [G], "blank": ("La", ["El", "Un"])},
                                {"es": ["El oso come pan"], "en": ["The bear eats bread", "The bear is eating bread"], "c": [G], "blank": ("El", ["La", "Una"])},
                                {"es": ["Una araña y un pez"], "en": ["A spider and a fish"], "c": [G, ACC], "blank": ("Una", ["Un", "El"])},
                            ],
                        },
                    ],
                },
                {
                    "title": "To be", "icon": "✨", "concepts": ["verb.ser", PRON],
                    "lessons": [
                        {
                            "words": [("soy", "I am", "🙋", ["verb.ser"]), ("eres", "you are", "🫵", ["verb.ser"]),
                                      ("es", "he is", "👉", ["verb.ser"]), ("somos", "we are", "👫", ["verb.ser"])],
                            "sentences": [
                                {"es": ["Nosotros somos niños", "Somos niños"], "en": ["We are boys", "We are children", "We are kids"], "c": ["verb.ser", PRON], "blank": ("somos", ["son", "soy"])},
                                {"es": ["El gato es un animal"], "en": ["The cat is an animal"], "c": ["verb.ser", G], "blank": ("es", ["eres", "somos"])},
                                {"es": ["Tú eres un niño"], "en": ["You are a boy", "You are a child"], "c": ["verb.ser", ACC], "blank": ("eres", ["es", "soy"])},
                            ],
                        },
                        {
                            "words": [("el estudiante", "the student", "🎒", [G]), ("el médico", "the doctor", "🩺", [G, ACC]),
                                      ("el amigo", "the friend", "🤝", [G]), ("la amiga", "the friend (f)", "👭", [G])],
                            "sentences": [
                                {"es": ["Yo soy estudiante", "Soy estudiante"], "en": ["I am a student", "I am student"], "c": ["verb.ser"], "blank": ("soy", ["es", "eres"])},
                                {"es": ["Él es médico"], "en": ["He is a doctor"], "c": ["verb.ser", ACC], "blank": ("es", ["soy", "somos"])},
                                {"es": ["Ella es mi amiga"], "en": ["She is my friend"], "c": ["verb.ser", G], "blank": ("amiga", ["amigo", "amigos"])},
                                {"es": ["Somos amigos", "Nosotros somos amigos"], "en": ["We are friends"], "c": ["verb.ser"], "blank": ("Somos", ["Son", "Soy"])},
                            ],
                        },
                    ],
                },
                {"kind": "chest", "title": "Treasure", "icon": "🎁"},
                {
                    "title": "Adjectives", "icon": "🎨", "concepts": ["grammar.adjective_agreement"],
                    "lessons": [
                        {
                            "words": [("grande", "big", "🐘", ["grammar.adjective_agreement"]), ("pequeño", "small", "🐭", ["grammar.adjective_agreement", ACC]),
                                      ("rojo", "red", "🔴", ["grammar.adjective_agreement"]), ("bonito", "pretty", "🌸", ["grammar.adjective_agreement"])],
                            "sentences": [
                                {"es": ["El gato es pequeño"], "en": ["The cat is small", "The cat is little"], "c": ["grammar.adjective_agreement", ACC], "blank": ("pequeño", ["pequeña", "pequeños"])},
                                {"es": ["La manzana es roja"], "en": ["The apple is red"], "c": ["grammar.adjective_agreement"], "blank": ("roja", ["rojo", "rojos"])},
                                {"es": ["El perro es grande"], "en": ["The dog is big", "The dog is large"], "c": ["grammar.adjective_agreement"], "blank": ("El", ["La", "Las"])},
                                {"es": ["La niña es pequeña"], "en": ["The girl is small", "The girl is little"], "c": ["grammar.adjective_agreement", ACC], "blank": ("pequeña", ["pequeño", "pequeños"])},
                            ],
                        },
                        {
                            "words": [("alto", "tall", "🦒", ["grammar.adjective_agreement"]), ("nuevo", "new", "✨", ["grammar.adjective_agreement"]),
                                      ("feliz", "happy", "😊", ["grammar.adjective_agreement"]), ("blanco", "white", "⚪", ["grammar.adjective_agreement"])],
                            "sentences": [
                                {"es": ["El hombre es alto"], "en": ["The man is tall"], "c": ["grammar.adjective_agreement"], "blank": ("alto", ["alta", "altos"])},
                                {"es": ["La mujer es alta"], "en": ["The woman is tall"], "c": ["grammar.adjective_agreement"], "blank": ("alta", ["alto", "altas"])},
                                {"es": ["El gato es blanco"], "en": ["The cat is white"], "c": ["grammar.adjective_agreement"], "blank": ("blanco", ["blanca", "blancas"])},
                                {"es": ["La niña es feliz"], "en": ["The girl is happy"], "c": ["grammar.adjective_agreement", ACC], "blank": ("La", ["El", "Los"])},
                            ],
                        },
                    ],
                },
                {
                    "title": "Plurals", "icon": "🔢", "concepts": ["grammar.plurals", G],
                    "lessons": [
                        {
                            "words": [("los gatos", "the cats", "🐈", ["grammar.plurals", G]), ("las manzanas", "the apples", "🍏", ["grammar.plurals", G]),
                                      ("los niños", "the boys", "👬", ["grammar.plurals", G, ACC]), ("las mujeres", "the women", "👯", ["grammar.plurals", G])],
                            "sentences": [
                                {"es": ["Los gatos comen"], "en": ["The cats eat", "The cats are eating"], "c": ["grammar.plurals", "verb.comer_beber"], "blank": ("Los", ["Las", "El"])},
                                {"es": ["Las niñas beben agua"], "en": ["The girls drink water", "The girls are drinking water"], "c": ["grammar.plurals", ACC], "blank": ("Las", ["Los", "La"])},
                                {"es": ["Los perros son grandes"], "en": ["The dogs are big", "The dogs are large"], "c": ["grammar.plurals", "grammar.adjective_agreement"], "blank": ("grandes", ["grande", "grando"])},
                                {"es": ["Las manzanas son rojas"], "en": ["The apples are red"], "c": ["grammar.plurals", "grammar.adjective_agreement"], "blank": ("rojas", ["rojos", "roja"])},
                            ],
                        },
                    ],
                },
                {"kind": "trophy", "title": "Unit 2 review", "icon": "🏆"},
            ],
        },
        {
            "title": "Talk about family and places",
            "description": "Use tener, questions and negation",
            "color": "#4F6BF5",
            "guidebook": [
                {"es": "Yo tengo un hermano", "en": "I have a brother"},
                {"es": "¿Dónde está el gato?", "en": "Where is the cat?"},
                {"es": "No tengo un perro", "en": "I don't have a dog"},
            ],
            "skills": [
                {
                    "title": "Family", "icon": "👨‍👩‍👧", "concepts": ["vocab.family", "verb.tener"],
                    "lessons": [
                        {
                            "words": [("la madre", "the mother", "👩", [G]), ("el padre", "the father", "👨", [G]),
                                      ("el hermano", "the brother", "👦", [G]), ("la hermana", "the sister", "👧", [G])],
                            "sentences": [
                                {"es": ["Mi madre bebe café"], "en": ["My mother drinks coffee", "My mom drinks coffee"], "c": ["vocab.family", ACC], "blank": ("madre", ["padre", "hermano"])},
                                {"es": ["Mi padre es alto"], "en": ["My father is tall", "My dad is tall"], "c": ["vocab.family", "grammar.adjective_agreement"], "blank": ("alto", ["alta", "altos"])},
                                {"es": ["Ella es mi hermana"], "en": ["She is my sister"], "c": ["vocab.family", "verb.ser"], "blank": ("hermana", ["hermano", "hermanos"])},
                            ],
                        },
                        {
                            "words": [("tengo", "I have", "🤲", ["verb.tener"]), ("tienes", "you have", "🫴", ["verb.tener"]),
                                      ("tiene", "she has", "👐", ["verb.tener"]), ("la familia", "the family", "👪", [G])],
                            "sentences": [
                                {"es": ["Yo tengo un hermano", "Tengo un hermano"], "en": ["I have a brother"], "c": ["verb.tener", G], "blank": ("tengo", ["tiene", "tienes"])},
                                {"es": ["Tú tienes un gato", "Tienes un gato"], "en": ["You have a cat"], "c": ["verb.tener", ACC], "blank": ("tienes", ["tengo", "tiene"])},
                                {"es": ["Ella tiene una hermana"], "en": ["She has a sister"], "c": ["verb.tener", G], "blank": ("tiene", ["tengo", "tienes"])},
                                {"es": ["Mi familia es grande"], "en": ["My family is big", "My family is large"], "c": ["vocab.family"], "blank": ("es", ["son", "eres"])},
                            ],
                        },
                    ],
                },
                {
                    "title": "Places", "icon": "🏠", "concepts": ["vocab.places", G],
                    "lessons": [
                        {
                            "words": [("la casa", "the house", "🏠", [G]), ("la escuela", "the school", "🏫", [G]),
                                      ("la ciudad", "the city", "🏙️", [G]), ("la playa", "the beach", "🏖️", [G]),
                                      ("el restaurante", "the restaurant", "🍽️", [G])],
                            "sentences": [
                                {"es": ["La casa es grande"], "en": ["The house is big", "The house is large"], "c": ["vocab.places", G], "blank": ("La", ["El", "Los"])},
                                {"es": ["La escuela es nueva"], "en": ["The school is new"], "c": ["vocab.places", "grammar.adjective_agreement"], "blank": ("nueva", ["nuevo", "nuevos"])},
                                {"es": ["Mi ciudad es bonita"], "en": ["My city is pretty", "My city is beautiful", "My city is nice"], "c": ["vocab.places", "grammar.adjective_agreement"], "blank": ("bonita", ["bonito", "bonitos"])},
                                {"es": ["Yo como en el restaurante", "Como en el restaurante"], "en": ["I eat in the restaurant", "I eat at the restaurant"], "c": ["vocab.places", "verb.comer_beber"], "blank": ("el", ["la", "los"])},
                            ],
                        },
                    ],
                },
                {"kind": "chest", "title": "Treasure", "icon": "🎁"},
                {
                    "title": "Questions", "icon": "❓", "concepts": ["grammar.word_order", ACC],
                    "lessons": [
                        {
                            "words": [("qué", "what", "🤔", ["grammar.word_order", ACC]), ("dónde", "where", "📍", ["grammar.word_order", ACC]),
                                      ("cómo", "how", "🧐", ["grammar.word_order", ACC]), ("quién", "who", "🕵️", ["grammar.word_order", ACC])],
                            "sentences": [
                                {"es": ["¿Dónde está el gato?"], "en": ["Where is the cat?"], "c": ["grammar.word_order", ACC], "blank": ("Dónde", ["Qué", "Quién"])},
                                {"es": ["¿Qué comes?", "¿Qué comes tú?"], "en": ["What do you eat?", "What are you eating?"], "c": ["grammar.word_order", ACC], "blank": ("Qué", ["Dónde", "Quién"])},
                                {"es": ["¿Cómo estás?"], "en": ["How are you?"], "c": ["grammar.word_order", ACC], "blank": ("Cómo", ["Qué", "Dónde"])},
                                {"es": ["¿Quién es ella?"], "en": ["Who is she?"], "c": ["grammar.word_order", ACC], "blank": ("Quién", ["Qué", "Cómo"])},
                            ],
                        },
                        {
                            "words": [("el libro", "the book", "📖", [G]), ("la carta", "the letter", "✉️", [G])],
                            "sentences": [
                                {"es": ["No tengo un perro", "Yo no tengo un perro"], "en": ["I do not have a dog", "I don't have a dog"], "c": ["grammar.word_order", "verb.tener"]},
                                {"es": ["Ella no bebe café"], "en": ["She does not drink coffee", "She doesn't drink coffee"], "c": ["grammar.word_order", ACC], "blank": ("no", ["sí", "es"])},
                                {"es": ["El niño no es alto"], "en": ["The boy is not tall", "The boy isn't tall"], "c": ["grammar.word_order", ACC]},
                                {"es": ["No tengo el libro", "Yo no tengo el libro"], "en": ["I do not have the book", "I don't have the book"], "c": ["grammar.word_order", G], "blank": ("el", ["la", "los"])},
                            ],
                        },
                    ],
                },
                {"kind": "trophy", "title": "Unit 3 review", "icon": "🏆"},
            ],
        },
    ],
}

ACHIEVEMENTS = [
    ("first_lesson", "First Steps", "Complete your first lesson", "👣", "#58CC02", "lessons", 1),
    ("scholar", "Scholar", "Complete 10 lessons", "📚", "#1CB0F6", "lessons", 10),
    ("wildfire_3", "Wildfire", "Reach a 3 day streak", "🔥", "#FF9600", "streak", 3),
    ("wildfire_7", "Wildfire II", "Reach a 7 day streak", "🔥", "#FF4B4B", "streak", 7),
    ("sage_100", "Sage", "Earn 100 XP", "⚡", "#FFC800", "total_xp", 100),
    ("sage_500", "Sage II", "Earn 500 XP", "⚡", "#FFC800", "total_xp", 500),
    ("sharpshooter", "Sharpshooter", "Complete a lesson with no mistakes", "🎯", "#CE82FF", "perfect", 1),
    ("perfectionist", "Perfectionist", "Complete 5 lessons with no mistakes", "💎", "#CE82FF", "perfect", 5),
    ("conqueror", "Conqueror", "Complete 3 levels", "👑", "#FFC800", "skills", 3),
    ("duo_student", "Smarto's Student", "Finish a personalized practice built by Smarto", "🦉", "#58CC02", "personalized", 1),
    ("legendary", "Legendary", "Pass a Legendary challenge", "🏅", "#FFC800", "legendary", 1),
]

BOTS = [
    ("lucia_m", "Lucía", "#FF4B4B", 52), ("kenji", "Kenji", "#1CB0F6", 44), ("amara.o", "Amara", "#CE82FF", 38),
    ("theo_b", "Theo", "#FF9600", 33), ("priya", "Priya", "#58CC02", 29), ("mateo", "Mateo", "#2B70C9", 25),
    ("sofia.r", "Sofía", "#FFC800", 21), ("noah_k", "Noah", "#FF86D0", 18), ("lena", "Lena", "#00CD9C", 15),
    ("omar_f", "Omar", "#A560E8", 12), ("yuki", "Yuki", "#FF4B4B", 10), ("diego", "Diego", "#1CB0F6", 8),
    ("hana", "Hana", "#58CC02", 6), ("felix", "Félix", "#FF9600", 4), ("zoe", "Zoe", "#CE82FF", 2),
]
