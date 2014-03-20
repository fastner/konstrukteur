@task
def build(regenerate = False):
	"""Generate source (development) version"""

	profile = Profile(session)
	profile.registerPart("$${name}", styleName="$${name}.Main")
	profile.setHashAssets(True)
	profile.setCopyAssets(True)

	konstrukteur.build(profile, regenerate)

	Build.run(profile)
