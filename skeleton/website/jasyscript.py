import konstrukteur.Konstrukteur

@task
def build(regenerate = False):
	"""Generate source (development) version"""

	# Initialize assets
	AssetManager.AssetManager(profile, session)

	# Build static website
	konstrukteur.Konstrukteur.build(regenerate)
