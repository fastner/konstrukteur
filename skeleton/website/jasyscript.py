from jasy.core.Profile import Profile
import jasy.build.Manager

@task
def build(regenerate = False):
	"""Generate pages"""

	profile = Profile(session)
	profile.registerPart("$${name}", styleName="$${name}.Main")
	profile.setHashAssets(True)
	profile.setCopyAssets(True)

	konstrukteur.build(profile, regenerate)

	jasy.build.Manager.run(profile)
