import konstrukteur.Konstrukteur

@task
def build(regenerate = False):
	"""Generate source (development) version"""

	konstrukteur.Konstrukteur.build(regenerate)
