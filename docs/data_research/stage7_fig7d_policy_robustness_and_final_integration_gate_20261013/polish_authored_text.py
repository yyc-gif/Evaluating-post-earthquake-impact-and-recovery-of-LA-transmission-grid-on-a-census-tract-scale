"""Mechanical readability pass on new drafts only; no source/numeric edits."""
import re
from common import *


def main():
    excluded = {'CURRENT_FORMAL_CAPTIONS_EXACT_EXTRACT.md', 'D1_FORMAL_DEFINITION_SOURCE_EXCERPTS.md'}
    replacements = {
        'R Q1':'RQ1', 'R Q2':'RQ2', 'R Q3':'RQ3',
        'Stage7':'Stage 7', 'Figure7':'Figure 7', 'FigureS9':'Figure S9',
        'partitions2299':'partitions 2,299', 'full2299-tract':'full 2,299-tract',
        'full2299':'full 2,299', 'only16':'only 16', 'max_iter500':'max_iter=500', 'tol1e-4':'tol=1e-4',
        'seeds42-46':'seeds 42-46', 'registeredK':'registered K', 'four geographic blocks':'four geographic blocks',
        'frozenSOVI':'frozen SOVI', 'frozenquartiles':'frozen quartiles', 'positive-populationcohort':'positive-population cohort',
        'H2matrix':'H2 matrix', 'K3primary':'K3 primary', 'K3main':'K3 main', 'K4sensitivity':'K4 sensitivity',
        'K4sens':'K4 sensitivity', 'sourceidentity':'source identity', 'sourcehashes':'source hashes',
        'data/preprocessing/IDs':'data/preprocessing/IDs',
        'authorapproval':'author approval', 'authorreview':'author review', 'authorchoices':'author choices',
        'activeeditablemanuscript':'active editable manuscript', 'activeworktree':'active worktree',
        'formalpromotion':'formal promotion', 'promotionbranch':'promotion branch', 'promotioncommit':'promotion commit',
        'backupbranch':'backup branch', 'currentGit':'current Git', 'LFSobjects':'LFS objects', 'originalarchives':'original archives',
        'sourcebytes':'source bytes', 'exactfiles':'exact files', 'codehashes':'code hashes',
        'newcandidate':'new candidate', 'oldfit':'old fit', 'savedcandidate':'saved candidate',
        'savedK3':'saved K3', 'savedK4':'saved K4', 'savedauthority':'saved authority', 'newsource':'new source',
        'newversion':'new version', 'newtypo':'new typo', 'newtypology':'new typology',
        'oldPCA':'old PCA', 'oldTop10':'old Top10', 'oldStage7':'old Stage 7', 'oldFormal_Experiment':'old Formal_Experiment',
        'differentlocal':'different local', 'source-exception':'source-exception',
        'fullcohort':'full cohort', 'new2299':'new 2299', 'only16':'only 16', 'forK3':'for K3',
        'referencepopulation':'reference population', 'K3/K4source':'K3/K4 source',
        'noimputation':'no imputation', 'noquartile':'no quartile', 'nosimulation':'no simulation',
        'lightweighttests':'lightweight tests', 'publicationwidth':'publication width', 'everyaffectedpage':'every affected page',
        'fittingorsimulation':'fitting or simulation', 'manifest-boundlocalarchives':'manifest-bound local archives',
        'finaldiff':'final diff', 'figurecopies':'figure copies', 'captionpages':'caption pages', 'manuscriptbytes':'manuscript bytes',
        'unrelatedpaperedits':'unrelated paper edits', 'unrelatedscientifichashes':'unrelated scientific hashes',
        'coordinateddrafts':'coordinated drafts', 'coordinatedreplacement':'coordinated replacement',
        'Stage7texts':'Stage 7 texts', 'textpointers':'text pointers', 'frozenpopulation':'frozen population',
        'statisticalandInit-source':'statistical and Init-source', 'statisticalconfidence':'statistical confidence',
        'geographiclimitations':'geographic limitations', 'sourcegeography':'source geography',
        'significant-hotspot':'significant-hotspot', 'repairpriority':'repair priority', 'priorityscore':'priority score',
        'policychange':'policy change', 'policyset':'policy set', 'frozenQ4':'frozen Q4', 'QuartileQ4':'Quartile Q4',
        'Q4outline':'Q4 outline', 'P75cutoff':'P75 cutoff', 'partialcommon':'partial common',
        'continuousdeficit':'continuous deficit', 'supplementpaths':'supplement paths', 'supplementtargets':'supplement targets',
        'robustnessfigurenumber':'robustness figure number', 'robustnessnumbering':'robustness numbering',
        'oldhistory':'old history', 'originalquartiles':'original quartiles', 'originalstage':'original stage',
        'GitLFSobjects':'Git LFS objects', 'GitLFS':'Git LFS', 'hashit':'hash it',
        'fromexacttimestampedcopies':'from exact timestamped copies', 'verifiedbackup':'verified backup',
        'fullset':'full set', 'corearithmetic':'core arithmetic', 'independentcorearithmetic':'independent core arithmetic',
        'operator/source':'operator/source', 'samecohort':'same cohort', 'sameapprovedgraphic':'same approved graphic',
        'samesource':'same source', 'exactsame':'exact same', 'allold':'all old', 'allnewassets':'all new assets',
        'threecolors':'three colors', 'sixdescriptive':'six descriptive',
    }
    targets = [p for p in OUT.glob('*.md') if p.name not in excluded]
    targets += list((OUT / 'drafts').glob('*.md'))
    changes = []
    for path in targets:
        before = lp(path).read_text()
        after = before
        # Protect exact source paths, identifiers and URLs inside Markdown code
        # tokens. Spacing replacements apply only to surrounding authored prose.
        parts = re.split(r'(`[^`]+`)', after)
        for i in range(0, len(parts), 2):
            for old, new in sorted(replacements.items(), key=lambda pair: -len(pair[0])):
                parts[i] = re.sub(r'(?<![\w/])' + re.escape(old) + r'(?![\w/])', new, parts[i])
            parts[i] = re.sub(r'\b(only|all|the|into|for|of|from|than|about|versus|over|at|to)(\d{1,4})\b', r'\1 \2', parts[i])
            parts[i] = re.sub(r'\b(and|in|of|is|a)(?=\d{1,4}(?:\.|\b))', r'\1 ', parts[i])
            parts[i] = re.sub(r'\b(\d{1,4}(?:,\d{3})?)(tracts|residents|people|years|policies|classes|coordinates|h)\b', r'\1 \2', parts[i])
        after = ''.join(parts)
        if after != before:
            lp(path).write_text(after, encoding='utf-8', newline='\n')
            changes.append(dict(file=path.relative_to(OUT).as_posix(), before_sha256=hashlib.sha256(before.encode()).hexdigest(), after_sha256=sha(path)))
    dump('DRAFT_READABILITY_PASS.json', dict(new_authored_markdown_only=True, numeric_data_unchanged=True, source_extracts_excluded=True, changes=changes))


if __name__ == '__main__':
    main()
